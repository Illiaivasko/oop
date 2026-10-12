#!/usr/bin/env python3
"""PreToolUse(Bash) hook: on a `git commit`, print the commit gate, optionally run a lint/fix command,
and BLOCK (exit 2) if the commit would ADD temporary debug output.

The command is parsed (cmdparse.py, next to this file), so every spelling counts: `git -C dir commit`, `git -c k=v commit`,
extra spaces, `bash -c '... git commit'`, `$(...)`, and a variable as the command word (`$g commit` is inspected as a
git commit). Quoted text is data: `echo "git commit"` and `-m "fix pytest config"` are not commits or test runs.
Inspected repo: the one named by -C / --git-dir / --work-tree (relative to the command's cwd and any `cd` before it),
else AGENT_REPO_DIR. Scanned: the staged diff, plus `-a` changes and paths a `git add` in the same command stages.

Config (env; only ~, $HOME and $CLAUDE_PROJECT_DIR are expanded, nothing is evaluated):
  AGENT_REPO_DIR        repo to inspect when the command names none (default: $CLAUDE_PROJECT_DIR, else cwd)
  AGENT_WORKSPACE       workspace; overrides are logged to <workspace>/overrides.log (default: $CLAUDE_PROJECT_DIR/.work)
  AGENT_PRECOMMIT_CMD   optional best-effort command run in the repo before the scan (e.g. a linter --fix)
  AGENT_COMMIT_RULES    one-line reminder printed on every commit (format, what may be staged)
  AGENT_CONTRACT_PATHS  space-separated pathspecs that define the API contract (DOC CHECK, warns only)
  AGENT_CONTRACT_DOC    the contract doc that must be edited alongside them
  AGENT_PROBE_CMD_RE    regex of local probe / test commands; a match runs health-preflight.sh (warns only)
  AGENT_DEBUG_RE        regex of temporary debug lines (default: DEBUG_RE)
A value still holding a template placeholder (an uppercase name in angle brackets) blocks the commit with CONFIG ERROR.
Override for an intentional debug line: [templog-ok] inside the -m message, or --no-verify; both are logged.
Internal error on a command that mentions commit -> exit 2 GATE ERROR (fail closed); otherwise exit 0.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

DEBUG_RE = (r"breakpoint\(\)|import pdb|pdb\.set_trace|\bprint\(|console\.log\(|debugger;|binding\.pry|dbg!\(|"
            r"fmt\.Print(ln|f)?\(|# ?(TEMP|DEBUG|HACK|XXX)\b|// ?(TEMP|DEBUG|HACK|XXX)\b|TEMP[ _]?LOG")
PLACEHOLDER = re.compile(r"(?<![?(])<[A-Z][A-Za-z0-9_-]*>")
CONFIG_VARS = ("AGENT_REPO_DIR", "AGENT_WORKSPACE", "AGENT_PRECOMMIT_CMD", "AGENT_COMMIT_RULES", "AGENT_CONTRACT_PATHS",
               "AGENT_CONTRACT_DOC", "AGENT_PROBE_CMD_RE", "AGENT_DEBUG_RE", "AGENT_HEALTH_URL")
GIT_PATH_OPTS = {"-C", "--git-dir", "--work-tree"}
GIT_VALUE_OPTS = {"-c", "--namespace", "--config-env", "--super-prefix"}
COMMIT_LONG_VALUE = {"--file", "--reuse-message", "--reedit-message", "--fixup", "--squash", "--author", "--date",
                     "--template", "--cleanup", "--trailer", "--pathspec-from-file", "--gpg-sign"}
RUNNER_WORDS = {"pytest", "py.test", "tox", "nox", "jest", "vitest", "mocha", "rspec", "phpunit", "ctest"}
RUNNER_SUBS = {"npm": {"test", "t"}, "yarn": {"test"}, "pnpm": {"test"}, "bun": {"test"}, "go": {"test"},
               "cargo": {"test"}, "dotnet": {"test"}, "mix": {"test"}, "deno": {"test"}, "make": {"test", "check"},
               "gradle": {"test"}, "gradlew": {"test"}, "mvn": {"test"}, "npx": RUNNER_WORDS, "bunx": RUNNER_WORDS}
PY_TEST_MODULES = {"pytest", "unittest", "nose2", "tox"}
COMMIT_SUBS = {"commit", "commit-tree"}
KNOWN_SUBS = COMMIT_SUBS | {"add", "status", "diff", "log", "show", "push", "pull", "fetch", "checkout", "switch", "branch",
                            "merge", "rebase", "reset", "restore", "stash", "tag", "rm", "mv", "config", "rev-parse",
                            "ls-files", "remote", "clone", "init", "help", "version", "worktree", "blame", "grep"}
ALIAS_DEPTH = 5
MAKEFILES = ("GNUmakefile", "makefile", "Makefile")
MAKE_RULE = re.compile(r"^([^\s:=#][^:=]*?)\s*::?(?!=)(.*)$")
INLINE_CODE = {"python": "-c", "node": "-e", "perl": "-e", "ruby": "-e", "bun": "-e"}
QUOTED = re.compile(r"""(['"`])((?:\\.|(?!\1).)*?)\1""", re.S)
CODE_LIST = re.compile(r"\[([^\[\]]*)\]")
GIT_CALL_ARGS = re.compile(r"""['"]git['"]\s*,\s*\[\s*['"]commit""")
UNTRACKED_MAX = 1_000_000
UNRESOLVED = "\0unresolved"


@dataclass
class GitCall:
    path_opts: list[str]
    sub: str
    args: list[str]
    cwd: str
    moved: bool               # a `cd` ran before it in the same command


@dataclass
class Commit:
    call: GitCall
    messages: list[str] = field(default_factory=list)
    no_verify: bool = False
    all_tracked: bool = False


class Blocked(Exception):
    pass


# ---------- config ----------
def expand(value: str) -> str:
    """Expand ~, $HOME and $CLAUDE_PROJECT_DIR only; never evaluates the value."""
    home = os.environ.get("HOME", "")
    project = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if value == "~" or value.startswith("~/"):
        value = home + value[1:]
    for name, val in (("CLAUDE_PROJECT_DIR", project), ("HOME", home)):
        value = value.replace("${" + name + "}", val).replace("$" + name, val)
    return value


def config_errors() -> list[str]:
    out = []
    for name in CONFIG_VARS:
        hit = PLACEHOLDER.search(os.environ.get(name, ""))
        if hit:
            out.append(f"CONFIG ERROR: placeholder {hit.group(0)} in {name} - set it in the project settings env "
                       f"(or remove it) before committing")
    return out


def env(name: str, default: str = "") -> str:
    return os.environ.get(name) or default


# ---------- command analysis ----------
def _alias_value(name: str, inline: dict[str, str], cwd: str, path_opts: list[str]) -> str | None:
    """`-c alias.X=...` on the command line wins, else `git config --get alias.X` as git would see it from cwd."""
    if name in inline:
        return inline[name]
    d = cwd
    for k in range(len(path_opts) - 1):
        if path_opts[k] == "-C":
            try:
                d = resolve_dir(d, path_opts[k + 1])
            except Blocked:
                return None
    probe = GitCall(path_opts, "", [], d, False)
    r = subprocess.run(["git", *_git_globals(probe), "config", "--get", f"alias.{name}"], cwd=d if os.path.isdir(d) else None,
                       capture_output=True, text=True, errors="replace")
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def git_calls(argv: list[str], cwd: str, moved: bool, depth: int = 0) -> list[GitCall]:
    """Git invocations in argv, aliases resolved (`git ci`, `git -c alias.c=commit c`, `!sh` aliases)."""
    head = argv[0] if argv else ""
    unknown = "$" in head or "`" in head
    if os.path.basename(head) != "git" and not unknown:
        return []
    path_opts, inline, i = [], {}, 1
    while i < len(argv):
        a = argv[i]
        if a in GIT_PATH_OPTS:
            path_opts += argv[i:i + 2]
            i += 2
        elif a in GIT_VALUE_OPTS:
            key, eq, val = (argv[i + 1] if i + 1 < len(argv) else "").partition("=")
            if a == "-c" and key.lower().startswith("alias.") and eq:
                inline[key[6:]] = val
            i += 2
        elif a.startswith(("--git-dir=", "--work-tree=")):
            path_opts.append(a)
            i += 1
        elif a.startswith("-C") and len(a) > 2:
            path_opts += ["-C", a[2:]]
            i += 1
        elif a.startswith("-"):
            i += 1
        else:
            break
    sub = argv[i] if i < len(argv) else ""
    if unknown and sub not in COMMIT_SUBS:
        return []
    if sub and sub not in KNOWN_SUBS and not sub.startswith("-") and depth < ALIAS_DEPTH:
        value = _alias_value(sub, inline, cwd, path_opts)
        if value is not None:
            return _expand_alias(argv, i, value, cwd, moved, depth)
    return [GitCall(path_opts, sub, argv[i + 1:], cwd, moved)]


def _expand_alias(argv: list[str], i: int, value: str, cwd: str, moved: bool, depth: int) -> list[GitCall]:
    import cmdparse
    if value.startswith("!"):
        calls = []
        for cmd in cmdparse.parse(value[1:] + " " + shlex.join(argv[i + 1:])):
            calls += git_calls(cmd.argv, cwd, moved, depth + 1)
        return calls
    try:
        words = shlex.split(value)
    except ValueError:
        words = value.split()
    return git_calls(argv[:i] + words + argv[i + 1:], cwd, moved, depth + 1)


def parse_commit(call: GitCall) -> Commit:
    c, args, i = Commit(call), call.args, 0
    while i < len(args):
        a = args[i]
        if a == "--":
            break
        if a.startswith("--"):
            name, eq, val = a.partition("=")
            if name == "--message":
                c.messages.append(val if eq else (args[i + 1] if i + 1 < len(args) else ""))
                i += 1 if eq else 2
                continue
            c.no_verify |= name == "--no-verify"
            c.all_tracked |= name == "--all"
            i += 2 if name in COMMIT_LONG_VALUE and not eq else 1
            continue
        if a.startswith("-") and len(a) > 1:
            step = 1
            for j, ch in enumerate(a[1:], start=1):
                if ch in "mFCct":
                    attached = a[j + 1:]
                    if ch == "m":
                        c.messages.append(attached or (args[i + 1] if i + 1 < len(args) else ""))
                    step = 1 if attached else 2
                    break
                c.no_verify |= ch == "n"
                c.all_tracked |= ch == "a"
            i += step
            continue
        i += 1
    return c


def is_test_run(argv: list[str]) -> bool:
    if not argv:
        return False
    name = os.path.basename(argv[0])
    if name in RUNNER_WORDS:
        return True
    if re.fullmatch(r"python[\d.]*", name):
        return "-m" in argv[1:-1] and argv[argv.index("-m") + 1] in PY_TEST_MODULES
    subs = RUNNER_SUBS.get(name)
    rest = [a for a in argv[1:] if not a.startswith("-")]
    if subs and rest:
        return rest[0] in subs or (rest[0] == "run" and len(rest) > 1 and rest[1].startswith("test"))
    return False


def resolve_dir(base: str, path: str) -> str:
    path = os.path.expandvars(os.path.expanduser(path))
    if "$" in path:
        raise Blocked(f"COMMIT BLOCKED: cannot resolve the repo path '{path}' - name the repo with a literal -C path.")
    return os.path.normpath(os.path.join(base, path))


def repo_dir(call: GitCall) -> str:
    d, named, ops, k = call.cwd, call.moved, call.path_opts, 0
    while k < len(ops):
        if ops[k] == "-C" and k + 1 < len(ops):
            d = resolve_dir(d, ops[k + 1])
        named = True
        k += 2 if ops[k] in GIT_PATH_OPTS else 1
    if named:
        if UNRESOLVED in d:
            raise Blocked("COMMIT BLOCKED: the commit runs after a `cd` to a path the gate cannot resolve - "
                          "name the repo with a literal -C path.")
        return d
    return os.path.normpath(expand(env("AGENT_REPO_DIR", env("CLAUDE_PROJECT_DIR", d))))


def _make_rules(path: Path) -> tuple[dict[str, tuple[list[str], list[str]]], str]:
    """{target: (prerequisites, recipe lines)} and the default target of a Makefile (best effort, no includes)."""
    rules: dict[str, tuple[list[str], list[str]]] = {}
    first, current = "", []
    for line in path.read_text(errors="replace").splitlines():
        if line.startswith("\t") and current:
            for t in current:
                rules[t][1].append(line.lstrip("\t").lstrip("@-+ ").replace("$$", "$"))
            continue
        m = MAKE_RULE.match(line)
        current = []
        if m:
            current = m.group(1).split()
            deps, _, inline_recipe = m.group(2).partition(";")
            for t in current:
                rules.setdefault(t, ([], []))[0].extend(deps.split())
                if inline_recipe.strip():
                    rules[t][1].append(inline_recipe.strip())
                first = first or ("" if t.startswith(".") else t)
    return rules, first


def _make_recipes(argv: list[str], cwd: str) -> tuple[list[str], str]:
    """Recipe lines `make [target...]` would run (named targets and their prerequisites, 3 levels), and make's cwd."""
    d, makefile, targets, i = cwd, None, [], 1
    while i < len(argv):
        a = argv[i]
        if a in {"-C", "--directory"} and i + 1 < len(argv):
            d, i = resolve_dir(d, argv[i + 1]), i + 2
            continue
        if a in {"-f", "--file", "--makefile"} and i + 1 < len(argv):
            makefile, i = argv[i + 1], i + 2
            continue
        if a.startswith(("--directory=", "--file=", "--makefile=")):
            name, _, val = a.partition("=")
            d, makefile = (resolve_dir(d, val), makefile) if name == "--directory" else (d, val)
        elif not a.startswith("-") and "=" not in a:
            targets.append(a)
        i += 1
    path = Path(d, makefile) if makefile else next((Path(d, m) for m in MAKEFILES if Path(d, m).is_file()), None)
    if not path or not path.is_file():
        return [], d
    rules, first = _make_rules(path)
    lines, seen, todo = [], set(), [(t, 0) for t in (targets or [first])]
    while todo:
        t, level = todo.pop(0)
        if t in seen or t not in rules or level > 3:
            continue
        seen.add(t)
        prereqs, recipe = rules[t]
        lines += recipe
        todo += [(p, level + 1) for p in prereqs]
    return lines, d


def _code_commands(code: str) -> list[str]:
    """Shell text inline python/node/perl/ruby code would run: quoted command strings and ['git', 'commit'] lists."""
    out = []
    for m in CODE_LIST.finditer(code):
        items = [q[1] for q in QUOTED.findall(m.group(1))]
        if items and os.path.basename(items[0]) == "git":
            out.append(shlex.join(items))
    if GIT_CALL_ARGS.search(code):
        out.append("git commit")
    out += [q[1] for q in QUOTED.findall(code) if re.search(r"\bgit\b", q[1])]
    return out


def indirect(cmd, cwd: str) -> list[tuple[list[str], str]]:
    """(argv, cwd) of commands a make recipe or inline interpreter code runs; the parser cannot see these as commands."""
    import cmdparse
    name, texts, where = cmd.name, [], cwd
    lang = re.sub(r"[\d.]+$", "", name)
    if name in {"make", "gmake"}:
        try:
            texts, where = _make_recipes(cmd.argv, cwd)
        except (OSError, Blocked):
            return []
    elif lang in INLINE_CODE:
        flag = INLINE_CODE[lang]
        code = "\n".join(cmd.heredocs)
        if flag in cmd.argv[1:-1]:
            code += "\n" + cmd.argv[cmd.argv.index(flag) + 1]
        texts = _code_commands(code)
    out = []
    for text in texts:
        try:
            out += [(c.argv, where) for c in cmdparse.parse(text, 1) if c.argv]
        except cmdparse.ParseError:
            continue
    return out


def analyse(commands: list, cwd: str) -> tuple[list[Commit], dict[str, list[list[str]]], bool]:
    """(commits, pathspecs staged by `git add` per repo dir, a test runner in the same command)."""
    commits, adds, runner, base = [], {}, False, cwd
    for cmd in commands:
        argv = cmd.argv
        runner = runner or is_test_run(argv)
        if cmd.depth == 0 and argv[:1] in (["cd"], ["pushd"]) and len(argv) > 1 and argv[1] != "-":
            try:
                base = resolve_dir(base, argv[1])
            except Blocked:
                base = UNRESOLVED
            continue
        for sub_argv, where in [(argv, base), *indirect(cmd, base)]:
            for call in git_calls(sub_argv, where, base != cwd or where != base):
                if call.sub in COMMIT_SUBS:
                    commits.append(parse_commit(call))
                elif call.sub == "add":
                    specs = [a for a in call.args if not a.startswith("-")]
                    try:
                        adds.setdefault(repo_dir(call), []).append(specs or ["."])
                    except Blocked:
                        continue
    return commits, adds, runner


# ---------- repo inspection ----------
def _git_globals(call: GitCall) -> list[str]:
    out, ops, k = [], call.path_opts, 0
    while k < len(ops):
        if ops[k] in {"--git-dir", "--work-tree"} and k + 1 < len(ops):
            out.append(f"{ops[k]}={ops[k + 1]}")
        elif ops[k] != "-C":
            out.append(ops[k])
        k += 2 if ops[k] in GIT_PATH_OPTS else 1
    return out


def git(repo: str, call: GitCall, *args: str) -> str:
    r = subprocess.run(["git", *_git_globals(call), *args], cwd=repo, capture_output=True, text=True, errors="replace")
    return r.stdout


def added_lines(repo: str, commit: Commit, adds: list[list[str]]) -> list[str]:
    no_ext = ("--no-ext-diff", "--no-textconv", "--no-color", "-U0")
    out = git(repo, commit.call, "diff", "--cached", *no_ext)
    if commit.all_tracked:
        out += git(repo, commit.call, "diff", *no_ext)
    for specs in adds:
        out += git(repo, commit.call, "diff", *no_ext, "--", *specs)
        untracked = git(repo, commit.call, "ls-files", "--others", "--exclude-standard", "-z", "--", *specs)
        for rel in filter(None, untracked.split("\0")):
            path = Path(repo, rel)
            if path.is_file() and path.stat().st_size < UNTRACKED_MAX:
                out += "\n".join("+" + ln for ln in path.read_text(errors="replace").splitlines()) + "\n"
    return [ln for ln in out.splitlines() if ln.startswith("+") and not ln.startswith("+++")]


def log_override(kind: str, commit: Commit, repo: str) -> str:
    ws = Path(expand(env("AGENT_WORKSPACE", env("CLAUDE_PROJECT_DIR", os.getcwd()) + "/.work")))
    if not ws.is_dir():
        return f"not logged: workspace {ws} does not exist"
    line = "\t".join((time.strftime("%Y-%m-%d %H:%M:%S"), "precommit-gate", kind, repo,
                      (commit.messages[0].splitlines() or [""])[0] if commit.messages else ""))
    with open(ws / "overrides.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")
    return f"logged to {ws / 'overrides.log'}"


def doc_check(repo: str, call: GitCall) -> None:
    paths, doc = env("AGENT_CONTRACT_PATHS"), env("AGENT_CONTRACT_DOC")
    if not (paths and doc):
        return
    touched = git(repo, call, "diff", "--cached", "--name-only", "--", *paths.split()).split()
    doc_path = Path(repo, expand(doc))
    fresh = doc_path.exists() and time.time() - doc_path.stat().st_mtime < 7200
    if touched and not fresh:
        print(f"DOC CHECK: this commit touches response/contract code ({' '.join(touched)}) but {doc_path.name} was not "
              "edited in the last 2 h. If a consumer of this contract sees any change (a new field, a changed shape, "
              "when it appears), update the doc and tell whoever consumes it.")


def inspect(commit: Commit, adds: dict[str, list[list[str]]]) -> None:
    repo = repo_dir(commit.call)
    if not os.path.isdir(repo):
        raise Blocked(f"COMMIT BLOCKED: the repo to inspect '{repo}' does not exist - fix AGENT_REPO_DIR or the -C path.")
    if subprocess.run(["git", *_git_globals(commit.call), "rev-parse", "--git-dir"], cwd=repo, capture_output=True).returncode:
        print(f"precommit-gate: {repo} is not a git repo - nothing to scan.")
        return
    if env("AGENT_PRECOMMIT_CMD"):
        print(f"--- {env('AGENT_PRECOMMIT_CMD')} ---")
        r = subprocess.run(["sh", "-c", env("AGENT_PRECOMMIT_CMD")], cwd=repo, capture_output=True, text=True,
                           errors="replace", timeout=600)
        print("\n".join((r.stdout + r.stderr).splitlines()[-8:]))
    doc_check(repo, commit.call)
    print(f"--- temp-debug scan ({repo}: staged{', -a' if commit.all_tracked else ''}"
          f"{', git add paths' if adds.get(repo) else ''}) ---")
    pattern = re.compile(env("AGENT_DEBUG_RE", DEBUG_RE))
    hits = [ln for ln in added_lines(repo, commit, adds.get(repo, [])) if pattern.search(ln)]
    if not hits:
        print("clean: no obvious temp debug lines staged.")
        return
    override = ("[templog-ok]" if any("[templog-ok]" in m for m in commit.messages)
                else "--no-verify" if commit.no_verify else "")
    if override:
        print(f"TEMP-DEBUG OVERRIDE {override}: {len(hits)} debug line(s) kept on purpose ({log_override(override, commit, repo)}):")
        print("\n".join(hits[:20]))
        return
    raise Blocked("COMMIT BLOCKED: possible TEMPORARY debug lines staged - remove them, or put [templog-ok] in the -m "
                  "message if they are intentional (it is logged):\n" + "\n".join(hits[:20]))


def probe_preflight(command: str) -> None:
    probe = env("AGENT_PROBE_CMD_RE")
    if not probe or PLACEHOLDER.search(probe):
        return
    try:
        matched = re.search(probe, command)
    except re.error:
        print(f"CONFIG ERROR: AGENT_PROBE_CMD_RE is not a valid regex: {probe}")
        return
    if matched:
        subprocess.run(["bash", str(HERE / "health-preflight.sh")])


def gate(data: dict) -> int:
    command = (data.get("tool_input") or {}).get("command") or ""
    import cmdparse
    commits, adds, runner = analyse(cmdparse.parse(command), data.get("cwd") or os.getcwd())
    if not commits:
        probe_preflight(command)
        return 0
    errors = config_errors()
    if errors:
        raise Blocked("\n".join(errors) + "\nCOMMIT BLOCKED: the gate would scan the wrong repo or run a placeholder command.")
    if runner:
        raise Blocked("COMMIT BLOCKED: tests and the commit are in one command. Run the tests on their own, compare the "
                      "pass/fail count with the known failures, then commit in a separate command.")
    print("PRE-COMMIT GATE: lint + full test suite green + a guard test that FAILS on the old code. "
          f"Local commit only unless told to push. {env('AGENT_COMMIT_RULES')}".rstrip())
    for commit in commits:
        inspect(commit, adds)
    return 0


def main() -> int:
    raw = sys.stdin.read()
    try:
        return gate(json.loads(raw or "{}"))
    except Blocked as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:
        if re.search(r"commit", raw):
            print(f"GATE ERROR precommit-gate: {type(exc).__name__}: {exc}. Tell the human; do not work around it.",
                  file=sys.stderr)
            return 2
        return 0


if __name__ == "__main__":
    sys.exit(main())
