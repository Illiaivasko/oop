#!/usr/bin/env python3
"""PreToolUse hook (blocks) for Bash|Edit|Write|MultiEdit: stop "fake green" - removing or disabling tests instead of fixing code.

Blocks (exit 2, reason on stderr):
- Bash: rm / unlink / shred / trash / git rm of a test file or test dir (also behind timeout/sudo/env/nice/xargs,
  inside $(), bash -c, eval, or a heredoc fed to a shell); find <test path> -delete; mv / git mv of a test out of the
  test paths or to a disabled name (.bak, .disabled, ...); emptying an existing test (`> tests/x.py`, truncate,
  cp /dev/null); python/perl/ruby/node -c|-e or heredoc code that removes, renames, copies over or writes an existing
  test path.
- Bash: ANY write onto an existing test file - cp / install / rsync / ln / mv / tee onto it, dd of=, `git restore
  --source` / `git checkout <rev> -- <test>`, sed -i / perl -i / awk -i inplace (use the Edit tool: it is checked). A
  write whose new content is known (cp/mv/ln source, a heredoc) passes when it keeps every test (see below).
- Edit / MultiEdit / Write over an existing test file, judged on the whole file after the change: fewer test
  definitions (a removed or renamed-away test), more hollow tests (body only pass / ... / a docstring, `{}` in JS/Go),
  or an ADDED skip/xfail/only marker.
- Test collection switched off: conftest.py gaining collect_ignore / collect_ignore_glob / pytest_ignore_collect /
  pytest_collection_modifyitems, pytest.ini / pyproject.toml / setup.cfg / tox.ini gaining --ignore / --deselect / -k,
  package.json / jest config gaining testPathIgnorePatterns - by Edit/Write, a redirect, tee or sed -i.
Allowed: new tests, edits to test bodies/assertions, renames that stay tests, writing a new test file, deleting
fixtures/test data (fixtures/, testdata/, data/ dirs) and anything outside the project (e.g. /tmp/test_x.py),
`git checkout -- <test>` / `git restore <test>` (back to the index), appending (`>>`, tee -a).
The Bash command is parsed by cmdparse (core/hooks/cmdparse.py, installed next to this hook): quoted arguments and
heredoc bodies of non-shell commands are data, not commands.
Internal error (including a missing cmdparse) -> exit 2 with GATE ERROR (fail closed).

AGENT_TEST_GLOBS  ','-separated fnmatch globs of test paths (default: DEFAULT_GLOBS). A glob with '/' matches the
                  path relative to the project (at any depth); a glob without '/' matches the file name.
Adapted from karanb192/claude-code-hooks plugins/protect-tests (MIT, commit 3c9c90a60ea7).
"""
from __future__ import annotations

import fnmatch
import glob
import itertools
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_GLOBS = (
    "tests/*,test/*,__tests__/*,spec/*,specs/*,"
    "test_*.py,*_test.py,*_test.go,*_spec.rb,*Test.java,*Test.kt,*Tests.cs,"
    "*.test.js,*.test.jsx,*.test.ts,*.test.tsx,*.test.mjs,*.spec.js,*.spec.jsx,*.spec.ts,*.spec.tsx,*.spec.mjs"
)
DISABLED_SUFFIX = re.compile(r"(\.bak|\.old|\.orig|\.disabled|\.skip|\.skipped|\.ignore|\.tmp|~)$", re.I)
SKIP_MARKERS = [re.compile(p, re.M) for p in (
    r"pytest\.mark\.(skip|skipif|xfail)\b",
    r"\bpytest\.(skip|xfail)\s*\(",
    r"\bunittest\.(skip|skipIf|skipUnless|expectedFailure)\b",
    r"^\s*@(skip|skipIf|skipUnless|expectedFailure)\b",
    r"\bself\.skipTest\s*\(",
    r"@(Disabled|Ignore)\b",
    r"\b(it|test|describe|context|suite)\.(skip|only)\s*\(",
    r"(?<![\w.$])(xit|xtest|xdescribe|xcontext|fit|fdescribe)\s*\(",
    r"\bt\.Skip(Now|f)?\s*\(",
    r"#\[ignore\]",
    r"\[Ignore\]",
)]
TEST_DEFS = re.compile(
    r"^\s*(async\s+)?def\s+test|^\s*func\s+Test|^\s*@Test\b|#\[test\]|\[(Test|Fact|Theory)\]"
    r"|(?<![\w.$])(it|test)\s*\(\s*['\"`]", re.M)
HOLLOW_PY = re.compile(r"^(?P<ind>[ \t]*)(?:async[ \t]+)?def[ \t]+test\w*[ \t]*\(.*?\)[^:\n]*:[ \t]*(?P<inline>[^\n]*)$", re.M | re.S)
HOLLOW_JS = re.compile(r"(?<![\w.$])(?:it|test)\s*\(\s*(['\"`])[^'\"`]*\1\s*,\s*(?:async\s*)?"
                       r"(?:\([^)]*\)\s*=>|\w+\s*=>|function\s*\w*\s*\([^)]*\))\s*\{\s*\}")
HOLLOW_GO = re.compile(r"^\s*func\s+Test\w*\s*\([^)]*\)\s*\{\s*\}", re.M)
TRIVIAL_STMT = re.compile(r"^(pass|\.\.\.|return|(?:[rRbBuU]?(?:'{3}|\"{3}|'|\")).*)$")
COLLECTION_FILES = {"conftest.py", "pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini", "package.json"}
COLLECTION_OFF = re.compile(r"\bcollect_ignore(_glob)?\b|\bdef\s+pytest_(ignore_collect|collection_modifyitems)\b"
                            r"|--ignore(-glob)?\b|--deselect\b|(?<![\w-])-k\b|\btestPathIgnorePatterns\b")
DELETE_CMDS = {"rm", "unlink", "shred", "trash", "trash-put", "rmdir"}
COPY_CMDS = {"cp", "gcp", "install", "ginstall", "rsync", "ln", "gln"}
COPY_VALUE_OPTS = {"-t", "--target-directory", "-S", "--suffix", "-m", "--mode", "-o", "--owner", "-g", "--group",
                   "-e", "--rsh", "--exclude", "--include", "--filter"}
IN_PLACE = {"sed": re.compile(r"^(--in-place(=.*)?|-[a-zA-Z]*i.*)$"), "gsed": re.compile(r"^(--in-place(=.*)?|-[a-zA-Z]*i.*)$"),
            "perl": re.compile(r"^-[a-zA-Z]*i.*$"), "ruby": re.compile(r"^-[a-zA-Z]*i.*$")}
TRUNCATING = {">", ">|", "&>"}
NOT_TESTS = re.compile(r"(^|/)(fixtures?|testdata|test_data|data)(/|$)")
ARTIFACT = re.compile(r"(^|/)(__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|node_modules|\.coverage[^/]*|[^/]*\.py[co]|[^/]*\.log)(/|$)")
INLINE_CODE = {"python": "-c", "perl": "-e", "ruby": "-e", "node": "-e"}
CODE_REMOVES = re.compile(r"\b(remove|unlink|rmtree|rmdir|rm|rmSync|unlinkSync)\b", re.I)
CODE_WRITES = re.compile(r"\b(truncate|truncateSync|write_text|write_bytes|writeFileSync|writeFile|copyFileSync|copyFile|"
                         r"renameSync|symlinkSync|hardlink_to|symlink_to)\b|\bshutil\.(copy\w*|move)\b"
                         r"|\bos\.(rename|replace|link|symlink)\b|\.rename\s*\("
                         r"|open\s*\([^)]*,\s*(mode\s*=\s*)?['\"][wax]|\.open\s*\(\s*(mode\s*=\s*)?['\"][wax]")
QUOTED = re.compile(r"""['"`]([^'"`\n]+)['"`]""")

REASON = (
    "PROTECT-TESTS: {what}. Fix the code, not the test - deleting, renaming away or skipping a test makes the suite "
    "falsely green. If removing or disabling it is truly intended, stop and ask the human: they approve it and run it "
    "themselves."
)


# ---------- test paths ----------
def _globs() -> list[str]:
    raw = os.environ.get("AGENT_TEST_GLOBS") or DEFAULT_GLOBS
    return [g.strip() for g in raw.split(",") if g.strip()]


def _relative(path: str, root: str) -> str:
    """Path relative to the project; a path outside it comes back absolute."""
    path = os.path.expanduser(path.replace("\\", "/"))
    if root and os.path.isabs(path):
        norm, base = os.path.normpath(path), os.path.normpath(root)
        if norm == base or norm.startswith(base.rstrip("/") + "/"):
            rel = os.path.relpath(norm, base)
            path = "" if rel == "." else rel + ("/" if path.endswith("/") else "")
    elif root and path.startswith(".."):
        return os.path.normpath(os.path.join(root, path))
    return path[2:] if path.startswith("./") else path


def _name_match(path: str) -> bool:
    name = path.rstrip("/").rsplit("/", 1)[-1]
    return any(fnmatch.fnmatchcase(name, g) for g in _globs() if "/" not in g)


def _dir_match(path: str) -> bool:
    path = path.rstrip("/")
    for g in (g for g in _globs() if "/" in g):
        for candidate in (path, path + "/x"):
            if fnmatch.fnmatchcase(candidate, g) or fnmatch.fnmatchcase(candidate, "*/" + g):
                return True
    return False


def is_test_path(path: str, root: str = "") -> bool:
    path = _relative(path, root)
    return bool(path) and not os.path.isabs(path) and not ARTIFACT.search(path) and (_name_match(path) or _dir_match(path))


def _deletable_test(path: str, root: str) -> bool:
    """A test path whose removal counts: fixtures and test data may go."""
    return is_test_path(path, root) and not NOT_TESTS.search(_relative(path, root))


def _expand(operand: str, root: str) -> list[str]:
    if not any(ch in operand for ch in "*?["):
        return [operand]
    if os.path.isabs(operand):
        return [operand, *glob.glob(operand)]
    return [operand, *(os.path.relpath(p, root) for p in glob.glob(os.path.join(root, operand)))]


# ---------- bash ----------
def _load_cmdparse():
    here = Path(__file__).resolve().parent
    for d in (here, here.parents[2] / "hooks"):
        if (d / "cmdparse.py").is_file():
            sys.path.insert(0, str(d))
            break
    import cmdparse
    return cmdparse


def _operands(args: list[str]) -> list[str]:
    out, ended = [], False
    for a in args:
        if a == "--" and not ended:
            ended = True
            continue
        if a.startswith("-") and not ended:
            continue
        out.append(a)
    return out


def _git_sub(argv: list[str]) -> list[str]:
    rest = argv[1:]
    while rest and rest[0].startswith("-"):
        rest = rest[2:] if rest[0] in {"-C", "-c", "--git-dir", "--work-tree"} else rest[1:]
    return rest


def _rename_target(sources: list[str], dest: str, many: bool) -> list[tuple[str, str]]:
    into_dir = many or dest.endswith("/") or os.path.isdir(dest)
    return [(s, dest.rstrip("/") + "/" + s.rstrip("/").rsplit("/", 1)[-1] if into_dir else dest) for s in sources]


def _check_move(args: list[str], root: str) -> str | None:
    target = next((a.split("=", 1)[1] for a in args if a.startswith("--target-directory=")), None)
    if "-t" in args and args.index("-t") + 1 < len(args):
        target = args[args.index("-t") + 1]
    ops = [o for o in _operands(args) if o != target]
    if target is None:
        if len(ops) < 2:
            return None
        ops, target = ops[:-1], ops[-1]
    pairs = _rename_target(ops, target, len(ops) > 1 or "-t" in args)
    reason = _check_overwrite(pairs, root)
    if reason:
        return reason
    for src, dst in pairs:
        if not _deletable_test(src, root):
            continue
        outside = os.path.isabs(_relative(dst, root))
        if outside or DISABLED_SUFFIX.search(dst.rstrip("/")) or not is_test_path(dst, root):
            return f"moving test '{src}' to '{dst}' takes it out of the test suite"
        if _name_match(_relative(src, root)) and not _name_match(_relative(dst, root)):
            return f"renaming test '{src}' to '{dst}' - the new name is no longer collected as a test"
    return None


def _check_find(args: list[str], root: str) -> str | None:
    if "-delete" not in args and not any(a in DELETE_CMDS for a in args):
        return None
    roots = []
    for a in args:
        if a.startswith("-") or a in {"!", "(", ")"}:
            break
        roots.append(a)
    names = [args[i + 1] for i, a in enumerate(args[:-1]) if a in {"-name", "-iname", "-path", "-wholename"}]
    hits = [p for p in (names or roots) if _deletable_test(p, root)]
    return f"find deletes test files ({', '.join(hits)})" if hits else None


def _abs(path: str, root: str) -> str:
    return path if os.path.isabs(path) else os.path.join(root, path)


def _existing_test(path: str, root: str) -> bool:
    return _deletable_test(path, root) and os.path.isfile(_abs(path, root))


def _code_paths(code: str) -> list[str]:
    """Quoted strings in code plus adjacent pairs joined ('tests' / 'test_a.py' -> tests/test_a.py)."""
    pieces = QUOTED.findall(code)
    return pieces + [a.rstrip("/") + "/" + b.lstrip("/") for a, b in itertools.pairwise(pieces)]


def _check_inline_code(cmd, root: str) -> str | None:
    flag = INLINE_CODE.get(re.sub(r"[\d.]+$", "", cmd.name))
    if not flag:
        return None
    code = "\n".join(cmd.heredocs)
    if flag in cmd.argv[1:-1]:
        code += "\n" + cmd.argv[cmd.argv.index(flag) + 1]
    paths = [p for p in dict.fromkeys(_code_paths(code)) if _deletable_test(p, root)]
    removed = [p for p in paths if os.path.exists(_abs(p, root))] if CODE_REMOVES.search(code) else []
    written = [p for p in paths if os.path.isfile(_abs(p, root))] if CODE_WRITES.search(code) else []
    hits = list(dict.fromkeys(removed + written))
    if hits:
        return f"{cmd.name} code removes or overwrites test path(s) {', '.join(hits)}"
    return None


def _stdin_text(cmd) -> str | None:
    """What a command reads on stdin when the hook can see it: a heredoc / here-string, or an echo/printf before |."""
    if cmd.heredocs:
        return "\n".join(cmd.heredocs)
    if cmd.stdin_words:
        last = cmd.stdin_words[-1]
        if last and os.path.basename(last[0]) in {"echo", "printf"}:
            return " ".join(w for w in last[1:] if not w.startswith("-"))
    return None


def _collection_file(path: str, root: str) -> bool:
    rel = _relative(path, root)
    return not os.path.isabs(rel) and rel.rsplit("/", 1)[-1] in COLLECTION_FILES or bool(re.search(r"(^|/)jest\.config\.\w+$", rel))


def _collection_off(old: str | None, new: str) -> bool:
    return len(COLLECTION_OFF.findall(new)) > len(COLLECTION_OFF.findall(old or ""))


def _written_text(cmd) -> str:
    """Everything a write command could put in a file: its stdin, echo/printf words, inline sed scripts."""
    words = cmd.argv[1:] if cmd.name in {"echo", "printf", "sed", "gsed", "perl", "ruby", "awk", "gawk"} else []
    return "\n".join([_stdin_text(cmd) or "", *words])


def _check_collection_write(cmd, targets: list[str], root: str) -> str | None:
    for target in targets:
        if _collection_file(target, root):
            old = _read(_abs(target, root))
            if _collection_off(old, (old or "") + "\n" + _written_text(cmd)):
                return f"the command adds a test-collection exclusion to {target}"
    return None


def _emptied_by_redirect(cmd, root: str) -> str | None:
    writes = [t for op, t in cmd.redirects if op in TRUNCATING | {">>", "&>>"}]
    reason = _check_collection_write(cmd, writes, root)
    if reason:
        return reason
    for op, target in cmd.redirects:
        if op in TRUNCATING and _existing_test(target, root):
            old = _read(_abs(target, root)) or ""
            if not cmd.heredocs or _replaces_tests(old, "\n".join(cmd.heredocs)):
                return f"the redirect '{op} {target}' empties or overwrites test file {target}"
    return None


def _value_operands(args: list[str]) -> tuple[list[str], str | None]:
    """(operands, -t/--target-directory) of cp/install/rsync/ln, skipping option values."""
    out, target, i, ended = [], None, 0, False
    while i < len(args):
        a = args[i]
        if not ended and a == "--":
            ended = True
        elif not ended and a.startswith("--target-directory="):
            target = a.split("=", 1)[1]
        elif not ended and a in COPY_VALUE_OPTS:
            if a in {"-t", "--target-directory"} and i + 1 < len(args):
                target = args[i + 1]
            i += 1
        elif ended or not a.startswith("-") or a == "-":
            out.append(a)
        i += 1
    return out, target


def _new_content(src: str, dst: str, root: str, symlink: bool) -> str | None:
    if src == "/dev/null":
        return ""
    if symlink and not os.path.isabs(src):
        src = os.path.join(os.path.dirname(_abs(dst, root)), src)
    return _read(_abs(src, root))


def _check_overwrite(pairs: list[tuple[str, str]], root: str, symlink: bool = False) -> str | None:
    for src, dst in pairs:
        if not _existing_test(dst, root) or os.path.normpath(_abs(src, root)) == os.path.normpath(_abs(dst, root)):
            continue
        new = _new_content(src, dst, root, symlink)
        if new is None:
            return f"overwriting test file {dst} with '{src}', whose content the guard cannot check"
        reason = _replaces_tests(_read(_abs(dst, root)) or "", new)
        if reason:
            return f"overwriting test file {dst} with '{src}' {reason}"
    return None


def _check_copy(name: str, args: list[str], root: str) -> str | None:
    ops, target = _value_operands(args)
    if target is None:
        if len(ops) < 2:
            return None
        ops, target = ops[:-1], ops[-1]
    pairs = _rename_target(ops, target, len(ops) > 1 or os.path.isdir(_abs(target, root)))
    symlink = name in {"ln", "gln"} and any(re.match(r"^-[a-zA-Z]*s", a) or a == "--symbolic" for a in args)
    return _check_overwrite(pairs, root, symlink)


def _check_git_restore(sub: list[str], root: str) -> str | None:
    """`git restore --source=X <test>` and `git checkout <rev> -- <test>` put another version over a test."""
    args = sub[1:]
    if sub[0] == "restore":
        source = any(a.startswith(("--source", "-s")) for a in args)
        paths = _operands([a for i, a in enumerate(args) if not (i and args[i - 1] in {"-s", "--source"})])
    elif "--" in args:
        k = args.index("--")
        source = any(not a.startswith("-") for a in args[:k])
        paths = args[k + 1:]
    else:
        ops = _operands(args)
        source = len(ops) > 1 and not os.path.exists(_abs(ops[0], root))
        paths = ops[1:]
    hits = [p for p in paths if _deletable_test(p, root)]
    if source and hits:
        return f"checking out another version over test path(s) {', '.join(hits)}"
    return None


def _check_in_place(cmd, root: str) -> str | None:
    pattern = IN_PLACE.get(cmd.name)
    in_place = (pattern and any(pattern.match(a) for a in cmd.argv[1:])) or \
        (cmd.name in {"awk", "gawk"} and "inplace" in cmd.argv[1:])
    if not in_place:
        return None
    files = [a for a in cmd.argv[1:] if not a.startswith("-")]
    reason = _check_collection_write(cmd, files, root)
    hits = [f for f in files if _existing_test(f, root)]
    if reason or hits:
        return reason or f"{cmd.name} edits test file(s) {', '.join(hits)} in place - use the Edit tool (it is checked)"
    return None


def _check_stream_write(cmd, root: str) -> str | None:
    """tee (not -a) and dd of= write stdin over the file."""
    if cmd.name == "tee":
        files = [a for a in _operands(cmd.argv[1:])]
        reason = _check_collection_write(cmd, files, root)
        if reason or any(a in {"-a", "--append"} or re.match(r"^-[a-zA-Z]*a", a) for a in cmd.argv[1:]):
            return reason
        known = _stdin_text(cmd)
        for f in files:
            if _existing_test(f, root) and (known is None or _replaces_tests(_read(_abs(f, root)) or "", known)):
                return f"tee overwrites test file {f}"
    if cmd.name == "dd":
        hits = [a[3:] for a in cmd.argv[1:] if a.startswith("of=") and _existing_test(a[3:], root)]
        if hits:
            return f"dd overwrites test file(s) {', '.join(hits)}"
    return None


def check_command(cmd, root: str) -> str | None:
    reason = _emptied_by_redirect(cmd, root)
    if reason or not cmd.argv:
        return reason
    name, argv = cmd.name, cmd.argv
    if name == "git":
        sub = _git_sub(argv)
        if sub[:1] in (["restore"], ["checkout"]):
            return _check_git_restore(sub, root)
        if sub[:1] not in (["rm"], ["mv"]):
            return None
        name, argv = sub[0], sub
    args = argv[1:]
    if cmd.via_xargs:
        args = args + [w for stage in cmd.stdin_words for w in stage[1:]]
    if name in DELETE_CMDS:
        hits = [p for o in _operands(args) for p in _expand(o, root) if _deletable_test(p, root)]
        return f"deleting test file(s) {', '.join(dict.fromkeys(hits))}" if hits else None
    if name == "truncate":
        hits = [o for o in _operands(args) if _existing_test(o, root)]
        return f"truncating test file(s) {', '.join(hits)}" if hits else None
    if name in COPY_CMDS:
        return _check_copy(name, args, root)
    if name == "mv":
        return _check_move(args, root)
    if name == "find":
        return _check_find(args, root)
    return _check_in_place(cmd, root) or _check_stream_write(cmd, root) or _check_inline_code(cmd, root)


def check_bash(command: str, root: str) -> str | None:
    cmdparse = _load_cmdparse()
    try:
        commands = cmdparse.parse(command)
    except cmdparse.ParseError:
        words = [w.strip("'\"") for w in command.split()]
        risky = DELETE_CMDS | {"mv", "find", "truncate"}
        if any(w in risky for w in words) and any(is_test_path(w, root) for w in words):
            return "an unparseable command (unbalanced quotes) deletes or moves a test path"
        return None
    for cmd in commands:
        reason = check_command(cmd, root)
        if reason:
            return reason
    return None


# ---------- edits ----------
def _marker_count(text: str) -> int:
    return sum(len(m.findall(text or "")) for m in SKIP_MARKERS)


def added_marker(old: str, new: str) -> bool:
    return _marker_count(new) > _marker_count(old)


def _fewer_tests(old: str, new: str) -> bool:
    return not new.strip() or len(TEST_DEFS.findall(new)) < len(TEST_DEFS.findall(old))


def _hollow_py(text: str) -> int:
    """Python test functions whose body is only pass / ... / return / a docstring / comments."""
    lines, count = text.splitlines(), 0
    starts = {text.count("\n", 0, m.start()): m for m in HOLLOW_PY.finditer(text)}
    for idx, m in starts.items():
        ind = len(m.group("ind").expandtabs())
        body = [m.group("inline")] if m.group("inline").strip() else []
        for line in lines[idx + 1:]:
            if line.strip() and len(line) - len(line.lstrip()) <= ind:
                break
            body.append(line)
        stmts = [re.sub(r"\s+#.*$", "", b.strip()) for b in body if b.strip() and not b.strip().startswith("#")]
        count += all(TRIVIAL_STMT.match(st) for st in stmts)
    return count


def _hollow(text: str) -> int:
    return _hollow_py(text) + len(HOLLOW_JS.findall(text)) + len(HOLLOW_GO.findall(text))


def _replaces_tests(old: str, new: str) -> str | None:
    """Why new content loses tests that old had, or None."""
    if _fewer_tests(old, new):
        return "empties it or drops test definitions"
    if _hollow(new) > _hollow(old):
        return "empties test bodies (pass / ... / {} only)"
    if added_marker(old, new):
        return "adds a skip/xfail/only marker"
    return None


def _read(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return None


def _apply_edits(text: str, edits: list[dict]) -> str | None:
    for e in edits:
        old, new = e.get("old_string") or "", e.get("new_string") or ""
        if not old or old not in text:
            return None
        text = text.replace(old, new) if e.get("replace_all") else text.replace(old, new, 1)
    return text


def check_edit(tool: str, inp: dict, root: str) -> str | None:
    path = inp.get("file_path") or ""
    if tool == "Edit":
        edits = [inp]
    elif tool == "MultiEdit":
        edits = inp.get("edits") or []
    else:
        edits = []
    old = _read(_abs(path, root))
    if tool == "Write":
        new = inp.get("content") or ""
    else:
        new = _apply_edits(old, edits) if old is not None else None
        if new is None:
            old = "\n".join(e.get("old_string") or "" for e in edits)
            new = "\n".join(e.get("new_string") or "" for e in edits)
    if _collection_file(path, root) and _collection_off(old, new):
        return f"the change adds a test-collection exclusion (collect_ignore / --ignore / --deselect / -k) to {path}"
    if not is_test_path(path, root) or old is None:
        return None
    if tool == "Write" and not (old.strip() and _deletable_test(path, root)):
        return f"the edit adds a skip/xfail/only marker to test file {path}" if added_marker(old, new) else None
    reason = _replaces_tests(old, new) if _deletable_test(path, root) else (
        "adds a skip/xfail/only marker" if added_marker(old, new) else None)
    return f"the change to test file {path} {reason}" if reason else None


def check(data: dict) -> str | None:
    tool, inp = data.get("tool_name"), data.get("tool_input") or {}
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    if tool == "Bash":
        return check_bash(inp.get("command") or "", root)
    if tool in {"Edit", "MultiEdit", "Write"}:
        return check_edit(tool, inp, root)
    return None


def main() -> int:
    try:
        reason = check(json.loads(sys.stdin.read() or "{}"))
    except Exception as exc:  # fail closed: a broken guard must not wave a deletion through
        print(f"GATE ERROR protect-tests: {type(exc).__name__}: {exc}. Tell the human; do not work around it.", file=sys.stderr)
        return 2
    if reason:
        print(REASON.format(what=reason), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
