#!/usr/bin/env python3
"""Split a bash command into the simple commands it would run, for PreToolUse guards.

parse(command) -> list[Simple], flattened in source order:
- separators ; & && || | |& ( ) and newlines split commands; a pipeline keeps the words of its earlier stages;
- $(...), `...`, <(...) (also inside double quotes and unquoted heredoc bodies) are parsed as commands too;
- bash/sh -c '...', eval ..., and a shell fed by a heredoc, a here-string or `echo ... |` are parsed recursively;
- heredoc bodies of any other command are data (kept in Simple.heredocs, never parsed);
- `#` starts a comment only at the start of a word (a#b and http://x/#frag are words);
- `script` (BSD `script file cmd...` and util-linux `script -c cmd`) runs its command, parsed recursively;
- wrappers (sudo, env, timeout, nice, ionice, stdbuf, xargs, command, time, nohup, exec, xcrun, ...) and their option values,
  NAME=value assignments and reserved words (if, then, do, !, {, ...) are unwrapped from argv.
Variables are never expanded: `$g commit` keeps "$g" as the command word. Unbalanced quotes raise ParseError.
Stdlib only; a guard that imports it must fail closed when the import fails.
"""
from __future__ import annotations

import os
import re
import shlex
from dataclasses import dataclass, field

MAX_DEPTH = 4
SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "ash", "busybox"}
RESERVED = {"!", "{", "}", "if", "then", "else", "elif", "fi", "do", "done", "while", "until", "time"}
ASSIGNMENT = re.compile(r"^[A-Za-z_]\w*(\[[^\]]*\])?\+?=")
REDIRECT_OPS = ("&>>", "<<<", "<<-", "<<", "<>", ">>", ">|", ">&", "<&", "&>", ">", "<")
OPERATORS = ("&&", "||", ";;", "|&", ";", "&", "|", "(", ")", "\n")
WORD_BREAK = set(" \t\r\n;&|()<>")
PIPE_OPS = {"|", "|&"}

# wrapper -> options that take a value (a separate word, or attached as -uroot / --user=root)
WRAPPERS: dict[str, set[str]] = {
    "sudo": {"-u", "-g", "-h", "-p", "-C", "-D", "-r", "-t", "-U", "-T", "--user", "--group", "--host",
             "--prompt", "--chdir", "--close-from", "--role", "--type", "--other-user", "--command-timeout"},
    "doas": {"-u", "-C"},
    "env": {"-u", "-C", "-S", "--unset", "--chdir", "--split-string"},
    "timeout": {"-s", "-k", "--signal", "--kill-after"},
    "gtimeout": {"-s", "-k", "--signal", "--kill-after"},
    "nice": {"-n", "--adjustment"},
    "ionice": {"-c", "-n", "-p", "-P", "-u", "--class", "--classdata"},
    "stdbuf": {"-i", "-o", "-e", "--input", "--output", "--error"},
    "xargs": {"-I", "-n", "-P", "-d", "-E", "-L", "-s", "-a", "--max-args", "--max-procs", "--delimiter",
              "--arg-file", "--replace", "--max-lines", "--max-chars", "--eof", "--process-slot-var"},
    "command": set(), "builtin": set(), "nohup": set(), "time": set(), "exec": {"-a"},
    "caffeinate": {"-t", "-w"}, "chronic": set(), "unbuffer": set(), "setsid": set(), "noglob": set(),
    "xcrun": {"--sdk", "-sdk", "--toolchain", "-toolchain"},
}
LOOKUP_ONLY = {"command": {"-v", "-V"}, "xcrun": {"-f", "--find", "--show-sdk-path", "--show-sdk-version"}}
SCRIPT_VALUE_OPTS = {"-t", "-F", "-T", "-I", "-O", "-B", "-E", "-m", "--timing", "--log-in", "--log-out",
                     "--log-io", "--log-timing", "--echo", "--logging-format", "--output-limit"}
POSITIONAL_AFTER_OPTS = {"timeout": 1, "gtimeout": 1}


class ParseError(ValueError):
    pass


@dataclass
class Simple:
    argv: list[str]                  # command word + args after unwrapping (quotes removed, variables NOT expanded)
    words: list[str]                 # the raw words as written (wrappers included)
    redirects: list[tuple[str, str]] = field(default_factory=list)  # (op, target); heredoc target = its delimiter
    heredocs: list[str] = field(default_factory=list)               # heredoc / here-string bodies (stdin data)
    stdin_words: list[list[str]] = field(default_factory=list)      # words of the earlier stages of its pipeline
    via_xargs: bool = False          # operands also come from stdin (xargs): see stdin_words
    depth: int = 0                   # 0 = top level, >0 = inside $(), bash -c, eval, a shell's heredoc ...

    @property
    def name(self) -> str:
        return os.path.basename(self.argv[0]) if self.argv else ""


@dataclass
class _Tok:
    kind: str                        # word | op | redir
    value: str
    target: str = ""
    body: str | None = None
    quoted_delim: bool = False


@dataclass
class _Raw:
    words: list[str] = field(default_factory=list)
    redirects: list[tuple[str, str]] = field(default_factory=list)
    heredocs: list[str] = field(default_factory=list)
    subs: list[str] = field(default_factory=list)


# ---------- lexer ----------
def _match_paren(s: str, i: int) -> int:
    """Index of the ')' closing the '(' at s[i]; quotes and nested parens are skipped."""
    depth, j = 0, i
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == "'":
            k = s.find("'", j + 1)
            if k < 0:
                raise ParseError("unbalanced quote in $( )")
            j = k + 1
            continue
        if c == '"':
            j = _match_dquote(s, j) + 1
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return j
        j += 1
    raise ParseError("unbalanced $( )")


def _match_dquote(s: str, i: int) -> int:
    j = i + 1
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == '"':
            return j
        if c == "$" and s.startswith("$(", j):
            j = _match_paren(s, j + 1) + 1
            continue
        if c == "`":
            k = _match_backtick(s, j)
            j = k + 1
            continue
        j += 1
    raise ParseError("unbalanced double quote")


def _match_backtick(s: str, i: int) -> int:
    j = i + 1
    while j < len(s):
        if s[j] == "\\":
            j += 2
            continue
        if s[j] == "`":
            return j
        j += 1
    raise ParseError("unbalanced backtick")


def _substitution(s: str, i: int, subs: list[str]) -> tuple[str, int]:
    """At s[i] == '$' or '`': return (literal text, next index) and record the inner command."""
    if s[i] == "`":
        k = _match_backtick(s, i)
        subs.append(s[i + 1:k].replace("\\`", "`"))
        return s[i:k + 1], k + 1
    if s.startswith("$((", i):
        k = _match_paren(s, i + 1)
        return s[i:k + 1], k + 1
    k = _match_paren(s, i + 1)
    subs.append(s[i + 2:k])
    return s[i:k + 1], k + 1


def subs_in_text(text: str) -> list[str]:
    """Command substitutions in text that the shell expands (a double-quoted string, an unquoted heredoc body)."""
    subs, i = [], 0
    while i < len(text):
        c = text[i]
        if c == "\\":
            i += 2
        elif (c == "$" and text.startswith("$(", i)) or c == "`":
            _, i = _substitution(text, i, subs)
        else:
            i += 1
    return subs


def _lex(s: str) -> tuple[list[_Tok], list[list[str]]]:
    """Tokens plus, per token index, the substitutions found in that word."""
    toks: list[_Tok] = []
    tok_subs: list[list[str]] = []
    word: list[str] = []
    in_word = False
    subs: list[str] = []
    pending: list[_Tok] = []          # heredocs waiting for their body at the next newline
    want_target: _Tok | None = None
    i, n = 0, len(s)

    def end_word() -> None:
        nonlocal word, in_word, subs, want_target
        if not in_word:
            return
        text = "".join(word)
        if want_target is not None:
            want_target.target = text
            if want_target.value in ("<<", "<<-"):
                pending.append(want_target)
            elif want_target.value == "<<<":
                want_target.body = text
            want_target = None
            tok_subs[-1].extend(subs)
        else:
            toks.append(_Tok("word", text))
            tok_subs.append(list(subs))
        word, in_word, subs = [], False, []

    def read_bodies(j: int) -> int:
        for tok in pending:
            dash = tok.value == "<<-"
            lines = []
            while j <= n:
                nl = s.find("\n", j)
                line = s[j:] if nl < 0 else s[j:nl]
                j = n + 1 if nl < 0 else nl + 1
                if (line.lstrip("\t") if dash else line) == tok.target:
                    break
                lines.append(line)
            tok.body = "\n".join(lines)
            if not tok.quoted_delim:
                idx = next(k for k, t in enumerate(toks) if t is tok)
                tok_subs[idx].extend(subs_in_text(tok.body))
        pending.clear()
        return min(j, n)

    while i < n:
        c = s[i]
        if c == "\\" and i + 1 < n:
            if s[i + 1] == "\n":
                i += 2
                continue
            word.append(s[i + 1])
            in_word = True
            i += 2
            continue
        if c == "#" and not in_word:
            nl = s.find("\n", i)
            i = n if nl < 0 else nl
            continue
        if c in " \t\r":
            end_word()
            i += 1
            continue
        if c == "\n":
            end_word()
            want_target = None
            toks.append(_Tok("op", "\n"))
            tok_subs.append([])
            i = read_bodies(i + 1) if pending else i + 1
            continue
        if c == "'":
            k = s.find("'", i + 1)
            if k < 0:
                raise ParseError("unbalanced single quote")
            word.append(s[i + 1:k])
            in_word = True
            if want_target is not None and want_target.value in ("<<", "<<-"):
                want_target.quoted_delim = True
            i = k + 1
            continue
        if c == "$" and s.startswith("$'", i):
            k = i + 2
            buf = []
            while k < n and s[k] != "'":
                if s[k] == "\\" and k + 1 < n:
                    buf.append({"n": "\n", "t": "\t", "\\": "\\", "'": "'"}.get(s[k + 1], s[k + 1]))
                    k += 2
                    continue
                buf.append(s[k])
                k += 1
            if k >= n:
                raise ParseError("unbalanced $' quote")
            word.append("".join(buf))
            in_word = True
            i = k + 1
            continue
        if c == '"':
            k = _match_dquote(s, i)
            inner = s[i + 1:k]
            subs.extend(subs_in_text(inner))
            word.append(re.sub(r'\\([$`"\\\n])', r"\1", inner))
            in_word = True
            if want_target is not None and want_target.value in ("<<", "<<-"):
                want_target.quoted_delim = True
            i = k + 1
            continue
        if (c == "$" and s.startswith("$(", i)) or c == "`":
            text, i = _substitution(s, i, subs)
            word.append(text)
            in_word = True
            continue
        if c in "<>" and s.startswith("(", i + 1):
            k = _match_paren(s, i + 1)
            subs.append(s[i + 2:k])
            word.append(s[i:k + 1])
            in_word = True
            i = k + 1
            continue
        if c in WORD_BREAK:
            fd = "".join(word) if in_word and "".join(word).isdigit() and not subs else None
            op = next((o for o in REDIRECT_OPS if s.startswith(o, i)), None)
            if op and fd is not None:
                word, in_word = [], False
            else:
                end_word()
            if op:
                tok = _Tok("redir", op)
                toks.append(tok)
                tok_subs.append([])
                want_target = tok
                i += len(op)
                continue
            op = next(o for o in OPERATORS if s.startswith(o, i))
            want_target = None
            toks.append(_Tok("op", op))
            tok_subs.append([])
            i += len(op)
            continue
        word.append(c)
        in_word = True
        i += 1
    end_word()
    if pending:
        read_bodies(n)
    return toks, tok_subs


def _build(toks: list[_Tok], tok_subs: list[list[str]]) -> list[list[_Raw]]:
    pipelines: list[list[_Raw]] = []
    pipeline: list[_Raw] = []
    cur = _Raw()

    def close(pipe_continues: bool) -> None:
        nonlocal cur, pipeline
        if cur.words or cur.redirects or cur.subs:
            pipeline.append(cur)
        cur = _Raw()
        if not pipe_continues and pipeline:
            pipelines.append(pipeline)
            pipeline = []

    for tok, subs in zip(toks, tok_subs):
        cur.subs.extend(subs)
        if tok.kind == "word":
            cur.words.append(tok.value)
        elif tok.kind == "redir":
            cur.redirects.append((tok.value, tok.target))
            if tok.body is not None:
                cur.heredocs.append(tok.body)
        else:
            close(tok.value in PIPE_OPS)
    close(False)
    return pipelines


# ---------- unwrapping ----------
def _skip_options(args: list[str], value_opts: set[str]) -> tuple[list[str], list[str]]:
    """(rest after the wrapper's options, -S strings for env)."""
    split, i = [], 0
    while i < len(args):
        a = args[i]
        if a == "--":
            return args[i + 1:], split
        if not a.startswith("-") or a == "-":
            break
        name = a.split("=", 1)[0]
        if name in value_opts and "=" not in a:
            if name in {"-S", "--split-string"} and i + 1 < len(args):
                split.append(args[i + 1])
            i += 2
            continue
        if a.startswith("--split-string=") or (a.startswith("-S") and len(a) > 2 and not a.startswith("--")):
            split.append(a.split("=", 1)[1] if a.startswith("--") else a[2:])
        i += 1
    return args[i:], split


def _lookup_only(base: str, args: list[str]) -> bool:
    """`command -v x`, `xcrun -f x`: the wrapper looks the command up instead of running it."""
    flags, i = LOOKUP_ONLY.get(base, set()), 0
    while flags and i < len(args) and args[i].startswith("-"):
        if args[i] in flags:
            return True
        i += 2 if args[i] in WRAPPERS[base] else 1
    return False


def unwrap(words: list[str]) -> tuple[list[str], bool]:
    """Strip assignments, reserved words and wrapper commands; (argv, operands-come-from-stdin)."""
    argv, via_xargs = list(words), False
    for _ in range(32):
        if not argv:
            break
        head = argv[0]
        base = os.path.basename(head)
        if ASSIGNMENT.match(head) or head in RESERVED:
            argv = argv[1:]
            continue
        if base not in WRAPPERS:
            break
        if _lookup_only(base, argv[1:]):
            return [], via_xargs
        rest, split = _skip_options(argv[1:], WRAPPERS[base])
        if base == "env":
            while rest and ASSIGNMENT.match(rest[0]):
                rest = rest[1:]
            for text in reversed(split):
                rest = text.split() + rest
        rest = rest[POSITIONAL_AFTER_OPTS.get(base, 0):]
        if base == "xargs":
            via_xargs = True
            rest = rest or ["echo"]
        argv = rest
    return argv, via_xargs


# ---------- nested commands ----------
def _shell_script(argv: list[str]) -> tuple[str | None, bool]:
    """(script after -c, whether the shell reads its script from stdin)."""
    c_flag, i = False, 1
    while i < len(argv):
        a = argv[i]
        if a in {"-o", "+o", "-O", "+O"}:
            i += 2
            continue
        if a == "--":
            i += 1
            break
        if a.startswith("-") and not a.startswith("--") and len(a) > 1:
            c_flag = c_flag or "c" in a[1:]
            i += 1
            continue
        if a.startswith(("--", "+")):
            i += 1
            continue
        break
    if c_flag:
        return (argv[i] if i < len(argv) else None), False
    return None, i >= len(argv) or (argv[i] == "-" if i < len(argv) else False)


def _script_command(argv: list[str]) -> list[str]:
    """`script -c 'cmd' [file]` (util-linux) or `script [opts] file cmd args...` (BSD/macOS) runs a command in a pty."""
    i = 1
    while i < len(argv):
        a = argv[i]
        short_c = a.startswith("-") and not a.startswith("--") and a.endswith("c")
        if (a == "--command" or short_c) and i + 1 < len(argv):
            return [argv[i + 1]]
        if a.startswith("--command="):
            return [a.split("=", 1)[1]]
        if a == "--":
            i += 1
            break
        if not a.startswith("-") or a == "-":
            break
        i += 2 if a in SCRIPT_VALUE_OPTS else 1
    rest = argv[i + 1:]
    return [shlex.join(rest)] if rest else []


def _nested(cmd: Simple, depth: int) -> list[str]:
    """Shell text this command executes as commands."""
    if depth >= MAX_DEPTH or not cmd.argv:
        return []
    name = cmd.name
    if name == "eval":
        return [" ".join(cmd.argv[1:])]
    if name == "script":
        return _script_command(cmd.argv)
    if name == "busybox" and cmd.argv[1:2] in (["sh"], ["ash"], ["bash"]):
        cmd = Simple(cmd.argv[1:], cmd.words, cmd.redirects, cmd.heredocs, cmd.stdin_words, cmd.via_xargs, depth)
        name = "sh"
    if name not in SHELLS:
        return []
    script, from_stdin = _shell_script(cmd.argv)
    if script is not None:
        return [script]
    if not from_stdin:
        return []
    out = list(cmd.heredocs)
    for op, target in cmd.redirects:
        if op == "<<<" and target not in out:
            out.append(target)
    if cmd.stdin_words:
        last = cmd.stdin_words[-1]
        argv, _ = unwrap(last)
        if argv and os.path.basename(argv[0]) in {"echo", "printf"}:
            out.append(" ".join(a for a in argv[1:] if not (a.startswith("-") and len(a) <= 3)))
    return out


def parse(command: str, depth: int = 0) -> list[Simple]:
    toks, tok_subs = _lex(command)
    out: list[Simple] = []
    for pipeline in _build(toks, tok_subs):
        earlier: list[list[str]] = []
        for raw in pipeline:
            for sub in raw.subs:
                if depth < MAX_DEPTH:
                    out.extend(parse(sub, depth + 1))
            argv, via_xargs = unwrap(raw.words)
            cmd = Simple(argv, raw.words, raw.redirects, raw.heredocs, list(earlier), via_xargs, depth)
            out.append(cmd)
            for text in _nested(cmd, depth):
                out.extend(parse(text, depth + 1))
            earlier.append(raw.words)
    return out


def command_words(command: str) -> list[list[str]]:
    """Just the unwrapped argv of every simple command (empty ones dropped)."""
    return [c.argv for c in parse(command) if c.argv]
