#!/usr/bin/env python3
"""Promote project improvements to the kit core - analysed, never automatic.

  promote.py log --item PATH --kind skill|gate|route|template|rule --tag TAG --note TEXT
        record a local improvement (improve-setup does this when it builds one)
  promote.py candidates
        score every logged local improvement; write this project's candidates to the machine registry
  promote.py draft --item PATH
        copy an item to <workspace>/improve/promote-drafts/<slug>-<hash>/ with a leak report and a proposal skeleton;
        the draft never enters the kit repo until it is universal (a numbered proposal moves the clean version into core/)

A candidate needs both (a) a universal miss class (core/improve/tags.yaml) and (b) no project words;
(c) the same tag + kind built in another existing project (registry) only raises its priority.
`draft` refuses secret-looking files (.env*, *.pem, *.key, id_*, key or token shapes) and anything outside the project.
Env: AGENT_WORKSPACE (default ./.work), AGENT_PROJECT (default: the workspace's parent dir name; [a-z0-9._-]{1,64}),
AGENTKIT_HOME (default ~/.agentkit: candidates/ registry and leak-words.txt).
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import SHAPES, USERINFO  # noqa: E402

KIT = Path(__file__).resolve().parent.parent.parent
TAGS = KIT / "core" / "improve" / "tags.yaml"
KINDS = ("skill", "gate", "route", "template", "rule")
PROJECT_NAME = re.compile(r"[a-z0-9._-]{1,64}")
SECRET_FILES = (".env", ".env.*", "*.env", "*.pem", "*.key", "*.p12", "*.pfx", "*.jks", "*.keystore", "id_*",
                ".netrc", ".npmrc", ".pypirc", "credentials*", "*.secret*")
FLAGS = {"--item", "--kind", "--tag", "--note"}


class UsageError(Exception):
    pass


def agentkit_home() -> Path:
    return Path(os.path.expanduser(os.environ.get("AGENTKIT_HOME") or "~/.agentkit"))


def registry_dir() -> Path:
    return agentkit_home() / "candidates"


def leak_words_file() -> Path:
    return agentkit_home() / "leak-words.txt"


def workspace() -> Path:
    return Path(os.path.expanduser(os.environ.get("AGENT_WORKSPACE") or str(Path.cwd() / ".work"))).resolve()


def project_dir() -> Path:
    return workspace().parent


def project() -> str:
    raw = os.environ.get("AGENT_PROJECT")
    name = raw if raw is not None else re.sub(r"[^a-z0-9._-]+", "-", project_dir().name.lower()).strip("-.")[:64]
    if not PROJECT_NAME.fullmatch(name or "") or name.startswith("."):
        raise UsageError(f"AGENT_PROJECT must match [a-z0-9._-]{{1,64}} and not start with '.', got {name!r}")
    return name


def short_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:8]


def registry_file() -> Path:
    """One file per project: name plus a hash of its folder, so two projects called `app` never share one."""
    return registry_dir() / f"{project()}-{short_hash(str(project_dir()))}.jsonl"


def log_path() -> Path:
    return workspace() / "improve" / "local-changes.jsonl"


def universal_tags() -> set[str]:
    return set(re.findall(r"^\s{2}([a-z-]+):", TAGS.read_text(), re.M))


def leak_words() -> list[str]:
    words = [project().lower()]
    if leak_words_file().exists():
        words += [w.strip().lower() for w in leak_words_file().read_text().splitlines() if w.strip() and not w.startswith("#")]
    return sorted(set(words))


def _files(path: Path) -> list[Path]:
    return [path] if not path.is_dir() else sorted(p for p in path.rglob("*") if p.is_file() or p.is_symlink())


def leaks(path: Path) -> list[str]:
    text = " ".join(p.read_text(errors="ignore").lower() for p in _files(path) if p.is_file())
    return [w for w in leak_words() if re.search(r"\b" + re.escape(w) + r"\b", text)]


def read_jsonl(path: Path, what: str) -> list[dict]:
    """Rows of a JSONL file; a bad line is skipped with a warning, never fatal."""
    rows = []
    for n, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            row = None
        if isinstance(row, dict):
            rows.append(row)
        else:
            print(f"warning: skipped bad line {n} in {what} {path}", file=sys.stderr)
    return rows


def entries() -> list[dict]:
    p = log_path()
    return [e for e in read_jsonl(p, "the local log") if {"item", "kind", "tag"} <= e.keys()] if p.exists() else []


def other_projects(tag: str, kind: str) -> list[str]:
    """Projects that built the same tag + kind; a row counts only if its recorded project folder still exists."""
    seen, own = [], str(project_dir())
    for f in sorted(registry_dir().glob("*.jsonl")) if registry_dir().is_dir() else []:
        if f == registry_file():
            continue
        for row in read_jsonl(f, "the registry"):
            where = row.get("project_dir")
            if not isinstance(where, str) or where == own or not Path(where).is_dir():
                continue
            if row.get("tag") == tag and row.get("kind") == kind:
                seen.append(str(row.get("project") or f.stem))
                break
    return seen


def score(entry: dict) -> dict:
    item = Path(entry["item"])
    words = leaks(item) if item.exists() else ["<missing item>"]
    elsewhere = other_projects(entry["tag"], entry["kind"])
    checks = {"universal_class": entry["tag"] in universal_tags(), "clean_of_project_words": not words,
              "seen_in_other_project": bool(elsewhere)}
    candidate = checks["universal_class"] and checks["clean_of_project_words"]
    return {**entry, "checks": checks, "leaks": words, "elsewhere": elsewhere, "candidate": candidate,
            "priority": "high" if candidate and elsewhere else "normal"}


def secret_reason(path: Path) -> str | None:
    """Why a file must never be copied into a draft, or None."""
    if any(fnmatch.fnmatch(path.name.lower(), pat) for pat in SECRET_FILES):
        return f"{path.name} looks like a secret file"
    text = path.read_text(errors="ignore") if path.is_file() else ""
    if any(rx.search(text) for rx in SHAPES) or USERINFO.search(text):
        return f"{path.name} holds a key or token shape"
    return None


def inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def cmd_log(args: dict) -> int:
    if args.get("--tag") not in universal_tags() and not args.get("--tag", "").startswith("project:"):
        print(f"--tag must be one of {sorted(universal_tags())} or 'project:<name>' for a domain-only class", file=sys.stderr)
        return 2
    if args["--kind"] not in KINDS:
        print(f"--kind must be one of {', '.join(KINDS)}", file=sys.stderr)
        return 2
    row = {"ts": time.strftime("%Y-%m-%d"), "item": str(Path(args["--item"]).expanduser().resolve()), "kind": args["--kind"],
           "tag": args["--tag"], "note": args.get("--note", ""), "project": project(), "project_dir": str(project_dir())}
    log_path().parent.mkdir(parents=True, exist_ok=True)
    with log_path().open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"logged {row['kind']} {Path(row['item']).name} [{row['tag']}]")
    return 0


def cmd_candidates() -> int:
    scored = [score(e) for e in entries()]
    registry_dir().mkdir(parents=True, exist_ok=True)
    rows = [{"tag": s["tag"], "kind": s["kind"], "item": Path(s["item"]).name, "project": project(),
             "project_dir": str(project_dir())} for s in scored if s["candidate"]]
    registry_file().write_text("".join(json.dumps(r) + "\n" for r in rows))
    for s in scored:
        flags = " ".join(f"{k}={'y' if v else 'n'}" for k, v in s["checks"].items())
        verdict = "CANDIDATE" if s["candidate"] else "local"
        extra = f" leaks: {', '.join(s['leaks'])}" if s["leaks"] else ""
        if s["priority"] == "high":
            extra += f" priority=high (also built in: {', '.join(s['elsewhere'])})"
        print(f"{verdict:<9} {s['kind']:<8} {Path(s['item']).name:<28} [{s['tag']}] {flags}{extra}")
    if not scored:
        print("no local improvements logged yet")
    return 0


def _draft_refusal(src: Path) -> str | None:
    root = project_dir().resolve()
    if not inside(src, root):
        return f"{src} is outside the project {root}"
    for f in _files(src):
        real = f.resolve()
        if not inside(real, root):
            return f"{f} points outside the project"
        reason = secret_reason(f) if real.is_file() else None
        if reason:
            return reason
    return None


def cmd_draft(args: dict) -> int:
    target = str(Path(args["--item"]).expanduser().resolve())
    match = next((score(e) for e in entries() if e["item"] == target), None)
    if not match:
        print("log the item first (promote.py log ...)", file=sys.stderr)
        return 2
    src = Path(target)
    refusal = _draft_refusal(src)
    if refusal:
        print(f"refused: {refusal} - a draft never copies secrets or files from outside the project", file=sys.stderr)
        return 2
    slug = re.sub(r"[^a-z0-9]+", "-", src.stem.lower()).strip("-") or "item"
    out = workspace() / "improve" / "promote-drafts" / f"{slug}-{short_hash(target)}"
    out.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, out / src.name, dirs_exist_ok=True) if src.is_dir() else shutil.copy2(src, out / src.name)
    (out / "PROPOSAL.md").write_text(f"""# DRAFT promote {src.name} from {project()} ({match['kind']}, [{match['tag']}])
Not in core yet. Make it universal, then move it into core/ with a numbered proposal through the kit gate.
- Why: {match['note']}
- Checks: {json.dumps(match['checks'])}
- Project words to remove: {', '.join(match['leaks']) or 'none'}
- Seen in other projects: {', '.join(match['elsewhere']) or 'no'}
- Evidence: <miss hits for [{match['tag']}], measurements from the project (block rate, cases)>
- Search: <ready solutions checked>
- Impact: `agentkit refs` of the core file it replaces or extends
- Proof: the project's tests rewritten without project data; doctor green; the leak check passes
- Rollback: git revert; projects keep their local copy until they upgrade
- After it lands: each project upgrades, re-runs its parity check, then deletes its local copy.
""")
    print(f"draft at {out} - leaks to remove: {', '.join(match['leaks']) or 'none'}")
    return 0


def parse_flags(rest: list[str]) -> dict:
    """--flag value pairs; an unknown flag or a flag without a value is a usage error, not a silent pairing."""
    args, i = {}, 0
    while i < len(rest):
        flag = rest[i]
        if flag not in FLAGS or i + 1 >= len(rest):
            raise UsageError(f"unexpected argument {flag!r}")
        args[flag] = rest[i + 1]
        i += 2
    return args


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    try:
        args = parse_flags(rest)
        project()
        if cmd == "log" and {"--item", "--kind", "--tag"} <= args.keys():
            return cmd_log(args)
        if cmd == "candidates" and not args:
            return cmd_candidates()
        if cmd == "draft" and "--item" in args:
            return cmd_draft(args)
    except UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
