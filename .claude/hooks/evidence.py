#!/usr/bin/env python3
"""Evidence receipts per acceptance criterion (AC).

  evidence.py run <KEY> <AC> -- <command...>     run it, write a signed receipt (exit code, tree state, AC hash, redacted tail)
  evidence.py manual <KEY> <AC> --evidence FILE  record a human-provided artefact (demo log, screenshot) by its hash
  evidence.py confirm <KEY> <AC>                 the human confirms the latest manual receipt (interactive terminal only)
  evidence.py accept-acs <KEY>                    the human accepts an AC set rewritten after its receipts (terminal only)
  evidence.py status <KEY>                        per AC: OK / OK(manual, unconfirmed) / MISSING / FAILED / FORGED /
                                                  STALE(code) / STALE(ac) / AC-CHANGED; exit 1 unless all OK

ACs live in <workspace>/tickets/<KEY>.md under "## Acceptance criteria" as "- AC1: text" or "- [AC1] text".
A receipt is valid only for the exact AC text and the exact content of the project it ran on: any later change makes it STALE.
The project is AGENT_REPO_DIR, else the git top level of CLAUDE_PROJECT_DIR, else of the cwd; outside git, the files in
AGENT_EVIDENCE_PATHS (default: the workspace's parent minus the workspace).
Receipts carry an HMAC from a per-machine key (~/.agentkit/receipt.key, AGENTKIT_HOME overrides). The agent can read that
key, so the signature raises the bar against hand-written receipts; it is not a security boundary.
A proof must be able to fail: commands that only echo, pass, sleep or read (ls, cat, test, git status, curl without
--fail) are refused after unwrapping nice/timeout/env/xargs/bash -c; AGENT_PROOF_ALLOW names project runners that count.
Once any receipt exists, rewriting or removing an AC shows AC-CHANGED until a human runs accept-acs. The terminal check
stops an agent's plain pipe, not a faked terminal (script, expect): that needs an agent-side Bash deny.
"""
from __future__ import annotations

import ast
import hashlib
import hmac
import json
import os
import re
import secrets
import shlex
import subprocess
import sys
import time
from pathlib import Path

AC_LINE = re.compile(r"^\s*[-*]\s*(?:\[(AC\d+)\]|(AC\d+)\s*[:.-])\s*(.+)$")
SECTION = re.compile(r"(?im)^##\s*acceptance(?:\s+criteria)?\b[^\n]*$")
TAIL_LINES = 20
MAX_FILES = 20000
CACHE_DIRS = {"__pycache__", ".pytest_cache", "node_modules", ".mypy_cache", ".ruff_cache", ".git"}
CACHE_SUFFIXES = (".pyc", ".pyo")
CACHE_PATHSPECS = [f":(exclude,glob)**/{d}/**" for d in sorted(CACHE_DIRS - {".git"})] + [":(exclude,glob)**/*.pyc"]

# --- redaction: provider shapes first, then secrets named by their key, then opaque strings by shape
SECRET_NAME = (r"(?:x-[\w-]+|[\w-]*(?:token|secret|passw(?:or)?d|api[_-]?key|access[_-]?key|private[_-]?key|credentials?"
               r"|cookie|session|authorization)|[\w-]*[_-](?:key|auth|pwd|sig|signature)|key|auth|sid|pwd|signature)")
BENIGN_HEADERS = {"accept", "accept-encoding", "accept-language", "cache-control", "connection", "content-length",
                  "content-type", "host", "origin", "referer", "user-agent"}
SHAPES = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\beyJ[\w-]+\.[\w-]+\.[\w-]*"),
    re.compile(r"\beyJ[\w-]{8,}"),
    re.compile(r"\b(?:AKIA|ASIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|APKA)[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_\w{20,})"),
    re.compile(r"\bglpat-[\w-]{20,}"),
    re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\bAIza[\w-]{30,}"),
    re.compile(r"\b(?:sk|rk|pk)_(?:live|test)_[0-9A-Za-z]{10,}|\bwhsec_[0-9A-Za-z]{10,}"),
    re.compile(r"\bsk-(?:ant-|proj-)?[\w-]{20,}"),
]
USERINFO = re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://[^/\s:@'\"]+:)[^/\s@'\"]+@")
CURL_USER = re.compile(r"(?<![\w-])(-u[ \t]*|--user[= \t][ \t]*)(['\"]?)([^:\s'\"]+):[^\s'\"]+")
HEADER_FLAG = re.compile(r"(?<![\w-])(-H[ \t]*|--header[= \t][ \t]*)(?:(['\"])([\w-]+)([ \t]*:[ \t]*)([^'\"\n]*)"
                         r"|()([\w-]+)([ \t]*:[ \t]*)((?i:(?:bearer|basic|digest|token|negotiate)[ \t]+)?[^\s'\"]*))")
FLAG_VALUE = r"""('[^'\n]*'|"[^"\n]*"|[^\s'"]+)"""
# --api-token X, --client-secret=X, --password X: any long flag named like a secret takes the next word as its value
SECRET_FLAG = re.compile(r"(?i)(?<![\w-])(--[\w-]*(?:token|secret|key|passw(?:or)?d|pwd)[\w-]*)([= \t][ \t]*)(?!-)" + FLAG_VALUE)
# mysql -pPASS (attached only: `-p name` prompts and names a database) and redis-cli -a PASS
MYSQL_P = re.compile(r"(?i)(\b(?:mysql\w*|mariadb\w*)\b[^\n|;&]*?[ \t]-p)" + FLAG_VALUE)
REDIS_A = re.compile(r"(\bredis-cli\b[^\n|;&]*?[ \t](?:-a|--pass)[ \t]+)" + FLAG_VALUE)
NAMED_COLON = re.compile(rf"(?i)\b({SECRET_NAME})(?![\w-])(['\"]?[ \t]*:[ \t]*)(['\"]?)(?![ \t]*\*\*\*)((?:(?![ \t]--?[A-Za-z])[^'\"\n])+)")
NAMED_ASSIGN = re.compile(rf"(?i)\b({SECRET_NAME})(?![\w-])([ \t]*=[ \t]*)(?![=\s])(['\"]?)([^\s'\"&;,]+)")
BEARER = re.compile(r"(?i)\b(bearer)([ \t]+)[^\s'\"]+")
BASIC = re.compile(r"(?i)\b(basic|digest|negotiate)([ \t]+)([A-Za-z0-9+/._~-]{6,}={0,2})")
HEX = re.compile(r"(?<![\w-])(?<!commit )(?=[0-9a-fA-F]*\d)(?=[0-9a-fA-F]*[a-fA-F])[0-9a-fA-F]{12,}(?![\w-])")
OPAQUE = re.compile(r"(?<![\w+/=.-])(?<!commit )[A-Za-z0-9+/=_-]{24,}(?![\w+/=-])")

# --- commands that prove nothing
NOOPS = {"true", ":", "echo", "printf", "sleep", "set", "cd", "export", "unset", "pushd", "popd", "shift", "wait"}
READ_ONLY = {"ls", "cat", "head", "tail", "pwd", "which", "test", "[", "[[", "type", "whoami", "date", "wc", "stat",
             "file", "printenv", "id", "uname", "hostname", "tree", "du", "df", "basename", "dirname", "realpath", "readlink"}
GIT_READ_ONLY = {"status", "log", "diff", "show", "branch", "rev-parse", "describe", "remote", "ls-files", "shortlog"}
GIT_VALUE_OPTS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
CURL_VALUE_LETTERS = set("dHXouAbceFTxwmrEKyYzCDPQtU")
PY_TRIVIAL_NAMES = {"print", "exit", "quit", "sys", "os", "True", "False", "None"}
SEPARATORS = {";", "&&", "||", "&", "|", ";;"}
MASKING_SEPARATORS = {";", "||", "&"}


def workspace() -> Path:
    raw = os.environ.get("AGENT_WORKSPACE") or str(Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()) / ".work")
    if re.search(r"<[A-Z][A-Z0-9_ -]*>", raw):
        raise SystemExit(f"CONFIG ERROR: placeholder in AGENT_WORKSPACE ({raw}) - set it (SETUP.md section 5)")
    return Path(os.path.expanduser(raw))


def sha(text: str | bytes) -> str:
    data = text.encode() if isinstance(text, str) else text
    return hashlib.sha256(data).hexdigest()[:16]


# --- redaction

def _random_piece(s: str, min_len: int) -> bool:
    has_digit, has_alpha = any(c.isdigit() for c in s), any(c.isalpha() for c in s)
    mixed = any(c.isupper() for c in s) and any(c.islower() for c in s)
    return len(s) >= min_len and has_digit and has_alpha and (mixed or len(s) >= 16)


def _case_flips(s: str) -> int:
    letters = [c.isupper() for c in s if c.isalpha()]
    return sum(a != b for a, b in zip(letters, letters[1:]))


def _opaque(m: re.Match) -> str:
    s = m.group(0)
    if re.fullmatch(r"[0-9a-fA-F]+", s):
        return s  # hex is HEX's call, which spares commit ids
    if re.search(r"[+/]", s) and len(s) >= 32 and _case_flips(s) * 5 >= len(s):
        return "***"  # base64 with few digits still flips case constantly; paths do not
    if not re.search(r"[/_.-]", s):
        return "***" if _random_piece(s, 24) else s
    # paths and identifiers are made of short words; a secret has at least one long random run
    return "***" if any(_random_piece(p, 12) for p in re.split(r"[/_.-]", s)) else s


def _header_flag(m: re.Match) -> str:
    quote, name, colon, value = m.group(2, 3, 4, 5) if m.group(3) else m.group(6, 7, 8, 9)
    if name.lower() in BENIGN_HEADERS or not value.strip():
        return m.group(0)
    return f"{m.group(1)}{quote}{name}{colon}***"


def _flag_value(m: re.Match) -> str:
    value = m.group(m.lastindex)
    quote = value[0] if value[:1] in ("'", '"') else ""
    return m.group(0)[:m.start(m.lastindex) - m.start(0)] + f"{quote}***{quote}"


def _basic(m: re.Match) -> str:
    v = m.group(3)
    looks_encoded = any(c.isdigit() for c in v) or v.endswith("=") or (sum(c.isupper() for c in v) >= 2 and v.lower() != v)
    return f"{m.group(1)}{m.group(2)}***" if looks_encoded else m.group(0)


def redact(text: str) -> str:
    for rx in SHAPES:
        text = rx.sub("***", text)
    text = USERINFO.sub(r"\1***@", text)
    text = CURL_USER.sub(r"\1\2\3:***", text)
    text = HEADER_FLAG.sub(_header_flag, text)
    text = SECRET_FLAG.sub(_flag_value, text)
    text = MYSQL_P.sub(_flag_value, text)
    text = REDIS_A.sub(_flag_value, text)
    text = NAMED_COLON.sub(r"\1\2\3***", text)
    text = NAMED_ASSIGN.sub(r"\1\2\3***", text)
    text = BEARER.sub(r"\1\2***", text)
    text = BASIC.sub(_basic, text)
    text = HEX.sub("***", text)
    return OPAQUE.sub(_opaque, text)


# --- project state

def _git(repo: Path, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, input=stdin)


def _toplevel(path: str | os.PathLike | None) -> Path | None:
    if not path or not Path(path).is_dir():
        return None
    out = _git(Path(path), "rev-parse", "--show-toplevel")
    return Path(out.stdout.strip()).resolve() if out.returncode == 0 and out.stdout.strip() else None


def _expand(raw: str) -> Path:
    return Path(os.path.expanduser(os.path.expandvars(raw)))


def project_base(cwd: Path | None = None) -> Path:
    return _expand(os.environ.get("CLAUDE_PROJECT_DIR") or str(cwd or Path.cwd())).resolve()


def resolve_root(cwd: Path | None = None) -> dict:
    """{"kind": "git", "repo": ...} or {"kind": "files", "paths": [...]}: what a receipt's state is computed over."""
    env_repo = os.environ.get("AGENT_REPO_DIR")
    if env_repo:
        repo = _toplevel(_expand(env_repo))
    else:
        project = os.environ.get("CLAUDE_PROJECT_DIR")
        repo = (_toplevel(_expand(project)) if project else None) or _toplevel(cwd or Path.cwd())
    if repo:
        return {"kind": "git", "repo": str(repo)}
    raw = os.environ.get("AGENT_EVIDENCE_PATHS")
    paths = [_expand(p) for p in raw.split(os.pathsep) if p] if raw else [workspace().parent]
    return {"kind": "files", "paths": [str(p.resolve()) for p in paths]}


def _is_cache(rel: str) -> bool:
    return any(p in CACHE_DIRS for p in rel.split("/")) or rel.endswith(CACHE_SUFFIXES)


def _workspace_prefix(root: Path) -> str | None:
    try:
        return workspace().resolve().relative_to(root).as_posix() + "/"
    except ValueError:
        return None


def _git_fingerprint(repo: Path) -> str | None:
    """Content of every tracked + untracked (not ignored) file, independent of HEAD: committing the proven tree keeps it OK."""
    if _toplevel(repo) != repo:
        return None
    skip = _workspace_prefix(repo)
    head = _git(repo, "rev-parse", "--verify", "-q", "HEAD").stdout.strip()
    blobs: dict[str, str] = {}
    if head:
        for line in _git(repo, "ls-tree", "-r", "-z", "HEAD").stdout.split("\0"):
            if "\t" in line:
                meta, path = line.split("\t", 1)
                blobs[path] = meta.split()[2]
        changed = _git(repo, "diff", "HEAD", "--no-renames", "--name-only", "-z").stdout.split("\0")
    else:
        changed = _git(repo, "ls-files", "-z").stdout.split("\0")
    untracked = _git(repo, "ls-files", "--others", "--exclude-standard", "-z", "--", ".", *CACHE_PATHSPECS).stdout.split("\0")
    for path in changed:
        blobs.pop(path, None)
    fresh = [p for p in dict.fromkeys(changed + untracked) if p and "\n" not in p and (repo / p).is_file()]
    if fresh:
        out = _git(repo, "hash-object", "--stdin-paths", stdin="\n".join(fresh) + "\n").stdout.split()
        blobs.update(zip(fresh, out))
    lines = sorted(f"{p}\0{b}" for p, b in blobs.items() if not _is_cache(p) and not (skip and p.startswith(skip)))
    return f"{head[:12] or 'nohead'}+{sha(chr(10).join(lines))}"


def _files_fingerprint(paths: list[str]) -> str | None:
    """Outside git: a content hash of the evidence paths, or None when they are too big to hash."""
    skip = str(workspace().resolve())
    entries, count = [], 0
    for base in paths:
        if Path(base).is_file():
            entries.append(f"{base}\0{sha(Path(base).read_bytes())}")
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if d not in CACHE_DIRS and os.path.join(dirpath, d) != skip)
            for name in sorted(filenames):
                full = os.path.join(dirpath, name)
                if name.endswith(CACHE_SUFFIXES) or not os.path.isfile(full):
                    continue
                count += 1
                if count > MAX_FILES:
                    return None
                entries.append(f"{full}\0{sha(Path(full).read_bytes())}")
    return sha("\n".join(entries))


def tree_state(root: dict) -> str | None:
    if root["kind"] == "git":
        fp = _git_fingerprint(Path(root["repo"]))
        return f"git:{fp}" if fp else None
    fp = _files_fingerprint(root["paths"])
    return f"files:{fp}" if fp else None


def _content(state: str | None) -> str | None:
    # HEAD is shown for humans; only the content part decides staleness
    return state.rsplit("+", 1)[-1] if state else None


# --- receipts and their signature

def agentkit_home() -> Path:
    return _expand(os.environ.get("AGENTKIT_HOME") or "~/.agentkit")


def receipt_key() -> bytes:
    path = agentkit_home() / "receipt.key"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write(secrets.token_hex(32))
        except FileExistsError:
            pass
    return path.read_bytes().strip()


def sign(receipt: dict) -> str:
    body = json.dumps({k: v for k, v in receipt.items() if k != "sig"}, sort_keys=True, ensure_ascii=False)
    return hmac.new(receipt_key(), body.encode(), hashlib.sha256).hexdigest()


def signed(receipt: dict) -> bool:
    sig = receipt.get("sig")
    return isinstance(sig, str) and hmac.compare_digest(sig, sign(receipt))


def read_acs(key: str) -> dict[str, str]:
    record = workspace() / "tickets" / f"{key}.md"
    if not record.exists():
        return {}
    parts = SECTION.split(record.read_text(), maxsplit=1)
    if len(parts) < 2:
        return {}
    body = re.split(r"(?m)^## ", parts[1], maxsplit=1)[0]
    acs = {}
    for line in body.splitlines():
        m = AC_LINE.match(line)
        if m:
            acs[m.group(1) or m.group(2)] = m.group(3).strip()
    return acs


def store(key: str) -> Path:
    return workspace() / "evidence" / f"{key}.jsonl"


def write_receipt(key: str, receipt: dict) -> dict:
    receipt["sig"] = sign(receipt)
    path = store(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(receipt, ensure_ascii=False) + "\n")
    return receipt


def receipts(key: str) -> list[dict]:
    """Every line; an unparseable one comes back as {} so status can flag the store as tampered."""
    path = store(key)
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            row = {}
        out.append(row if isinstance(row, dict) else {})
    return out


# --- commands that prove nothing

def _cmdparse():
    """cmdparse lives in core/hooks (kit layout) or next to this file (installed into .claude/hooks)."""
    here = Path(__file__).resolve().parent
    for d in (here, here.parent / "hooks"):
        if (d / "cmdparse.py").is_file() and str(d) not in sys.path:
            sys.path.append(str(d))
    import cmdparse
    return cmdparse


def proof_allowlist() -> set[str]:
    return {w for w in re.split(r"[\s,:;]+", os.environ.get("AGENT_PROOF_ALLOW", "")) if w}


def _git_subcommand(argv: list[str]) -> str:
    i = 1
    while i < len(argv) and argv[i].startswith("-"):
        i += 2 if argv[i] in GIT_VALUE_OPTS else 1
    return argv[i] if i < len(argv) else ""


def _python_code(argv: list[str]) -> str | None:
    """The -c code of a python command, else None."""
    for i, a in enumerate(argv[1:], 1):
        if a == "-c":
            return argv[i + 1] if i + 1 < len(argv) else ""
        if not a.startswith("-"):
            return None
    return None


def _python_is_vacuous(code: str) -> bool:
    """pass / constants / print / exit only: nothing that can fail on the behaviour under test."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False  # it fails when run, so it cannot fake a pass
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) or (isinstance(node, ast.Call) and node.args and not (
                isinstance(node.args[0], ast.Constant) and node.args[0].value in (0, None)) and _is_exit(node.func)):
            return False  # it always fails, so it cannot fake a pass
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names] + ([node.module] if isinstance(node, ast.ImportFrom) else [])
            if not set(names) <= PY_TRIVIAL_NAMES:
                return False
        elif isinstance(node, ast.Name) and node.id not in PY_TRIVIAL_NAMES:
            return False
        elif isinstance(node, (ast.Attribute, ast.Subscript, ast.Lambda, ast.FunctionDef, ast.ClassDef, ast.With,
                               ast.For, ast.While, ast.Try, ast.Await)) and not _is_sys_exit(node):
            return False
    return True


def _is_exit(func: ast.AST) -> bool:
    return (isinstance(func, ast.Name) and func.id in ("exit", "quit")) or _is_sys_exit(func)


def _is_sys_exit(node: ast.AST) -> bool:
    return (isinstance(node, ast.Attribute) and node.attr == "exit" and isinstance(node.value, ast.Name)
            and node.value.id == "sys")


def _curl_has_check(argv: list[str]) -> bool:
    for a in argv[1:]:
        if a in ("--fail", "--fail-with-body"):
            return True
        if a.startswith("-") and not a.startswith("--"):
            for ch in a[1:]:
                if ch == "f":
                    return True
                if ch in CURL_VALUE_LETTERS:
                    break
    return False


def _kind(argv: list[str]) -> str:
    """real | noop | read-only | curl-no-check for one unwrapped simple command."""
    if not argv:
        return "noop"
    name = os.path.basename(argv[0])
    if name in NOOPS or (name == "exit" and argv[1:] in ([], ["0"])):
        return "noop"
    if re.fullmatch(r"(?:python|pypy)[\d.]*", name):
        code = _python_code(argv)
        return "noop" if code is not None and _python_is_vacuous(code) else "real"
    allowed = proof_allowlist()
    if name in allowed or argv[0] in allowed:
        return "real"
    project_script = "/" in argv[0] and not argv[0].startswith("/")
    if not project_script and (name in READ_ONLY or (name == "git" and _git_subcommand(argv) in GIT_READ_ONLY)):
        return "read-only"
    if name == "curl" and not _curl_has_check(argv):
        return "curl-no-check"
    return "real"


def _is_container(cp, cmd) -> bool:
    """A shell running -c / stdin, or eval: its inner commands are parsed separately."""
    if cmd.name == "eval":
        return True
    if cmd.name not in cp.SHELLS:
        return False
    script, from_stdin = cp._shell_script(cmd.argv)
    return script is not None or from_stdin or any(re.fullmatch(r"-[A-Za-z]*c[A-Za-z]*", a) for a in cmd.argv[1:])


def _split_script(script: str) -> tuple[list[list[str]], list[str]] | None:
    lexer = shlex.shlex(script.replace("\n", " ; "), posix=True, punctuation_chars=";&|")
    try:
        tokens = list(lexer)
    except ValueError:
        return None
    commands, seps, cur = [], [], []
    for t in tokens:
        if t in SEPARATORS:
            commands.append(cur)
            seps.append(t)
            cur = []
        else:
            cur.append(t)
    commands.append(cur)
    while len(commands) > 1 and not commands[-1]:
        commands.pop()
        seps.pop()
    return commands, seps


def _masking_reason(cp, script: str) -> str | None:
    parsed = _split_script(script)
    if parsed is None:
        return None
    commands, seps = parsed
    last = cp.unwrap([t for t in commands[-1] if t not in ("(", ")", "{", "}")])[0]
    if seps and seps[-1] in MASKING_SEPARATORS and _kind(last) != "real":
        return f"'{seps[-1]} {' '.join(commands[-1])}' at the end hides the real exit code"
    if "|" in seps and "pipefail" not in script:
        return "a pipeline returns the LAST command's exit code - add 'set -o pipefail;' or drop the pipe"
    return None


def trivial_reason(command: list[str]) -> str | None:
    """Why this command cannot prove an AC, or None when it can. Wrappers (nice, timeout, env, xargs, sudo) and
    shells (bash -lc, sh -c, eval, heredocs) are unwrapped first; every simple command inside is classified."""
    if not command:
        return "empty command"
    try:
        cp = _cmdparse()
        simples = cp.parse(shlex.join(command))
    except ImportError as exc:
        return f"cmdparse.py is missing next to evidence.py ({exc}) - reinstall the kit hooks"
    except ValueError as exc:
        return f"the command cannot be parsed ({exc})"
    kinds, scripts = [], []
    for cmd in simples:
        if _is_container(cp, cmd):
            script = cp._shell_script(cmd.argv)[0] if cmd.name in cp.SHELLS else None
            scripts.append(script)
            continue
        kinds.append(_kind(cmd.argv))
    if "real" not in kinds:
        if "curl-no-check" in kinds:
            return "curl exits 0 on an HTTP error - add --fail (or -f), or check the body with a test"
        if "read-only" in kinds:
            return "it only reads or lists (ls, cat, test, git status...) - nothing in it can fail on the behaviour"
        return "it only echoes, sleeps, passes or returns 0"
    for script in scripts:
        reason = _masking_reason(cp, script) if script else None
        if reason:
            return reason
    return None


# --- commands

def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _root_fields(root: dict) -> dict:
    return {"repo": root.get("repo"), "paths": root.get("paths")}


def cmd_run(key: str, ac: str, command: list[str]) -> int:
    acs = read_acs(key)
    if ac not in acs:
        print(f"{ac} is not in tickets/{key}.md '## Acceptance criteria' - add it first", file=sys.stderr)
        return 2
    reason = trivial_reason(command)
    if reason:
        print(f"refused: `{redact(shlex.join(command))}` cannot prove {ac} ({reason}). Run the real check "
              "(a test, a curl, a script) whose exit code fails when the AC is not met.", file=sys.stderr)
        return 2
    root = resolve_root()
    before = tree_state(root)
    if before is None:
        print("refused: the project is not a git repo and has too many files to hash - set AGENT_REPO_DIR "
              "or AGENT_EVIDENCE_PATHS to the code this AC is about.", file=sys.stderr)
        return 2
    proc = subprocess.run(command, capture_output=True, text=True)
    output = (proc.stdout or "") + (proc.stderr or "")
    after = tree_state(root)
    write_receipt(key, {
        "type": "run", "key": key, "ac": ac, "ac_hash": sha(acs[ac]), "acs": ac_hashes(acs), "cmd": redact(shlex.join(command)),
        "exit": proc.returncode, "state": after, "changed_during_run": _content(before) != _content(after),
        **_root_fields(root), "ts": _now(), "output_sha": sha(output),
        "tail": redact("\n".join(output.splitlines()[-TAIL_LINES:])),
        **({"proof_allow": sorted(proof_allowlist())} if proof_allowlist() else {}),
    })
    sys.stdout.write(output)
    print(f"\nreceipt: {key} {ac} exit={proc.returncode} state={after}", file=sys.stderr)
    return proc.returncode


def cmd_manual(key: str, ac: str, evidence: str) -> int:
    acs = read_acs(key)
    path = Path(evidence).expanduser().resolve()
    if ac not in acs or not path.is_file():
        print(f"need {ac} in the ACs and an existing evidence file", file=sys.stderr)
        return 2
    if path.stat().st_size == 0:
        print(f"refused: {path} is empty - point to the real demo log or screenshot", file=sys.stderr)
        return 2
    if store(key).parent.resolve() in path.parents:
        print("refused: the evidence file must live outside the evidence store", file=sys.stderr)
        return 2
    root = resolve_root()
    write_receipt(key, {"type": "manual", "key": key, "ac": ac, "ac_hash": sha(acs[ac]), "acs": ac_hashes(acs), "evidence": str(path),
                        "evidence_sha": sha(path.read_bytes()), "exit": 0, "state": tree_state(root),
                        "changed_during_run": False, **_root_fields(root), "human_confirm": "pending", "ts": _now()})
    print(f"manual receipt: {key} {ac} <- {path.name} (unconfirmed until the human runs `evidence.py confirm {key} {ac}`)")
    return 0


def cmd_confirm(key: str, ac: str) -> int:
    if not sys.stdin.isatty():
        print("refused: confirm needs a human at an interactive terminal", file=sys.stderr)
        return 2
    manual = next((r for r in reversed(receipts(key)) if r.get("ac") == ac and r.get("type") == "manual" and signed(r)), None)
    if not manual:
        print(f"no signed manual receipt for {key} {ac}", file=sys.stderr)
        return 2
    path = Path(manual["evidence"])
    same = path.is_file() and sha(path.read_bytes()) == manual["evidence_sha"]
    print(f"{key} {ac}: {read_acs(key).get(ac, '?')}\nevidence: {path} ({'unchanged' if same else 'CHANGED or missing'})")
    if input("Type yes if you checked this evidence yourself: ").strip().lower() != "yes":
        print("not confirmed")
        return 1
    write_receipt(key, {"type": "confirm", "key": key, "ac": ac, "confirms": manual["sig"], "ts": _now()})
    print(f"confirmed: {key} {ac}")
    return 0


def ac_hashes(acs: dict[str, str]) -> dict[str, str]:
    return {ac: sha(text) for ac, text in acs.items()}


def cmd_accept_acs(key: str) -> int:
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        print("refused: accept-acs needs a human at an interactive terminal", file=sys.stderr)
        return 2
    acs = read_acs(key)
    if not acs:
        print(f"no '## Acceptance criteria' in tickets/{key}.md", file=sys.stderr)
        return 2
    pinned = pinned_acs(receipts(key))
    for ac, text in acs.items():
        mark = "new" if ac not in pinned else ("CHANGED" if pinned[ac] != sha(text) else "same")
        print(f"{ac:<6} {mark:<8} {text}")
    for ac in sorted(set(pinned) - set(acs)):
        print(f"{ac:<6} REMOVED")
    if input("Type yes if these ACs are what the ticket needs (you read the changes yourself): ").strip().lower() != "yes":
        print("not accepted")
        return 1
    write_receipt(key, {"type": "accept-acs", "key": key, "acs": ac_hashes(acs), "ts": _now()})
    print(f"accepted the AC set of {key}")
    return 0


# --- status

class _States:
    """The current content state per receipt root, computed once per status call."""

    def __init__(self, cwd: Path | None):
        self.current, self.base, self.cache = resolve_root(cwd), project_base(cwd), {}

    def get(self, root: dict) -> str | None:
        k = json.dumps(root, sort_keys=True)
        if k not in self.cache:
            self.cache[k] = tree_state(root)
        return self.cache[k]

    def code_verdict(self, r: dict) -> str | None:
        """None when the receipt's code state still matches, else the STALE reason."""
        if r.get("changed_during_run") or not r.get("state"):
            return "STALE(code)"
        if r.get("repo"):
            repo = Path(r["repo"])
            if self.current["kind"] == "git" and Path(self.current["repo"]) != repo:
                return "STALE(code)"
            if not (repo == self.base or self.base in repo.parents or repo in self.base.parents):
                return "STALE(code)"
            now = self.get({"kind": "git", "repo": r["repo"]})
        elif self.current["kind"] == "git":
            return "STALE(code)"  # a receipt made outside git does not count inside a repo
        else:
            now = self.get({"kind": "files", "paths": r.get("paths") or []})
        return None if now and _content(now) == _content(r["state"]) else "STALE(code)"


def pinned_acs(rows: list[dict]) -> dict[str, str]:
    """The AC hashes the receipts were made against: first seen per AC, reset by a human accept-acs."""
    pinned: dict[str, str] = {}
    for r in rows:
        if not signed(r):
            continue
        if r.get("type") == "accept-acs":
            pinned = dict(r.get("acs") or {})
        elif r.get("type") in ("run", "manual"):
            for ac, h in (r.get("acs") or {r["ac"]: r.get("ac_hash")}).items():
                pinned.setdefault(ac, h)
    return pinned


def status(key: str, cwd: Path | None = None) -> dict[str, str]:
    acs = read_acs(key)
    if not acs:
        return {}
    rows = receipts(key)
    tampered = any((not r.get("ac") and r.get("type") != "accept-acs") or (r.get("type") == "accept-acs" and not signed(r))
                   for r in rows)
    latest: dict[str, dict] = {}
    confirmed: set[str] = set()
    for r in rows:
        if r.get("type") == "confirm" and signed(r):
            confirmed.add(r.get("confirms"))
        elif r.get("ac"):
            latest[r["ac"]] = r
    pinned = pinned_acs(rows)
    states = _States(cwd)
    out = {}
    for ac, text in acs.items():
        r = latest.get(ac)
        if tampered or (r and not signed(r)):
            out[ac] = "FORGED"
        elif not r:
            out[ac] = "MISSING"
        elif r.get("ac_hash") != sha(text):
            out[ac] = "STALE(ac)"
        elif ac in pinned and pinned[ac] != sha(text):
            out[ac] = "AC-CHANGED"
        elif r.get("exit") != 0:
            out[ac] = "FAILED"
        else:
            stale = states.code_verdict(r)
            unconfirmed = r.get("type") == "manual" and r.get("sig") not in confirmed
            out[ac] = stale or ("OK(manual, unconfirmed)" if unconfirmed else "OK")
    for ac in pinned:
        if ac not in acs:
            out[ac] = "FORGED" if tampered else "AC-CHANGED(removed)"
    return out


def main(argv: list[str]) -> int:
    if len(argv) >= 4 and argv[0] == "run" and "--" in argv:
        i = argv.index("--")
        return cmd_run(argv[1], argv[2], argv[i + 1:])
    if len(argv) == 5 and argv[0] == "manual" and argv[3] == "--evidence":
        return cmd_manual(argv[1], argv[2], argv[4])
    if len(argv) == 3 and argv[0] == "confirm":
        return cmd_confirm(argv[1], argv[2])
    if len(argv) == 2 and argv[0] == "accept-acs":
        return cmd_accept_acs(argv[1])
    if len(argv) == 2 and argv[0] == "status":
        st = status(argv[1])
        if not st:
            print(f"{argv[1]}: no '## Acceptance criteria' in tickets/{argv[1]}.md")
            return 1
        for ac, s in st.items():
            print(f"{ac:<6} {s}")
        return 0 if all(s == "OK" for s in st.values()) else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
