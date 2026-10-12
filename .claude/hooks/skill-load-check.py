#!/usr/bin/env python3
"""Stop hook (blocks): a skill the router named this turn must be loaded since the last compaction, or skipped with a stated reason.

A load from before the last compaction does not count: that copy is truncated, so the work runs from memory.
Skips (`skip-skill <name>: <why>` in the reply) are logged to <workspace>/skill-skips.log for misses-check.py as
date, skill, redacted reason, prompt hash - never the prompt text. A skip that cannot be logged does not count.
A routed skill with no <dir>/<name>/SKILL.md in any skills dir (AGENT_SKILLS_DIR, $CLAUDE_PROJECT_DIR/.claude/skills,
~/.claude/skills) is not required and is logged as reason "not-installed"; with no project skills dir every name stays required.
The turn is read back to its start even past the usual tail size; a start beyond AGENT_TRANSCRIPT_CAP_MB is a GATE ERROR.
Repeat blocks, errors and the decision log: see gatekit.py.
"""
from __future__ import annotations
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

GATE = "skill-load-check"
try:
    import gatekit
    from config import project_dir, skills_dir, workspace
    from transcript_tail import blocks, is_user_prompt, tail_entries
except Exception as exc:  # a broken install must block, not exit 1 (non-blocking)
    print(json.dumps({"decision": "block", "reason": f"GATE ERROR {GATE}: {exc} - run agentkit doctor"}))
    sys.exit(0)

ROUTED = re.compile(r"LOAD NOW, before acting: (.*?)\.(?:\n|$)")
SKIP = re.compile(r"skip-skill ([a-z0-9-]+): ([^\n]+)")
REDACT = [
    (re.compile(r"(?i)\b(bearer|basic)\s+\S+"), r"\1 ***"),
    (re.compile(r"(?i)\b([\w-]*(?:token|secret|passw\w*|pwd|api[_-]?key|authorization|cookie)[\w-]*)\s*[:=]?\s*\S+"), r"\1 ***"),
    (re.compile(r"([\w.-]+)\s*=\s*\S+"), r"\1=***"),
    (re.compile(r"([\w.-]+):\s*(?=\S*\d)\S+"), r"\1: ***"),
    (re.compile(r"(?=[A-Za-z0-9_+/=.-]*\d)(?=[A-Za-z0-9_+/=.-]*[A-Za-z])[A-Za-z0-9_+/=.-]{8,}"), "***"),
]
REASON_MAX = 120
SKILL_NAME = re.compile(r"[a-z0-9][a-z0-9-]*")


def _named(turn: list[dict]) -> list[str]:
    names = []
    for entry in turn:
        hook = entry.get("attachment") or {}
        if hook.get("hookEvent") != "UserPromptSubmit":
            continue
        match = ROUTED.search(str(hook.get("content", "")))
        if match:
            names += [s.strip() for part in match.group(1).split(";") for s in part.split("+") if s.strip()]
    return names


def _loaded(span: list[dict]) -> set[str]:
    loaded = set()
    for entry in span:
        for b in blocks(entry):
            if b.get("type") == "tool_use" and b.get("name") == "Skill":
                loaded.add(str((b.get("input") or {}).get("skill", "")).split(":")[-1])
    return loaded


def _skips(turn: list[dict]) -> dict[str, str]:
    skips = {}
    for entry in turn:
        if entry.get("type") != "assistant":
            continue
        for b in blocks(entry):
            if b.get("type") == "text":
                skips.update(dict(SKIP.findall(str(b.get("text", "")))))
    return skips


def _prompt_text(entry: dict) -> str:
    return " ".join(str(b.get("text", "")) for b in blocks(entry) if b.get("type") == "text")


def redact(reason: str) -> str:
    for rx, repl in REDACT:
        reason = rx.sub(repl, reason)
    return reason.replace("\t", " ").strip()[:REASON_MAX]


def _is_boundary(entry: dict) -> bool:
    return entry.get("subtype") == "compact_boundary"


def check(path: str) -> tuple[list[str], dict[str, str], str]:
    """(named and not loaded since the last compaction, skips, prompt hash)."""
    entries = tail_entries(path, _is_boundary, required=is_user_prompt)
    start = max((i for i, e in enumerate(entries) if is_user_prompt(e)), default=-1)
    boundary = max((i for i, e in enumerate(entries) if _is_boundary(e)), default=0)
    turn = entries[start + 1:]
    loaded = _loaded(entries[boundary:])
    skips = _skips(turn)
    unloaded = [s for s in dict.fromkeys(_named(turn)) if s not in loaded]
    prompt = _prompt_text(entries[start]) if start >= 0 else ""
    return unloaded, skips, hashlib.sha256(prompt.encode()).hexdigest()[:8]


def _skill_dirs() -> list[Path]:
    """Project skills dirs that exist, plus ~/.claude/skills; none when the project has no skills dir."""
    project = [d for d in dict.fromkeys([skills_dir(), project_dir() / ".claude" / "skills"]) if d.is_dir()]
    user_dir = Path.home() / ".claude" / "skills"
    return project + [user_dir] if project and user_dir.is_dir() and user_dir not in project else project


def not_installed(names: list[str]) -> list[str]:
    """Routed names with no SKILL.md in any skills dir; none when the project has no skills dir (a broken install stays strict)."""
    dirs = _skill_dirs()
    if not dirs:
        return []
    return [n for n in names if SKILL_NAME.fullmatch(n) and not any((d / n / "SKILL.md").is_file() for d in dirs)]


def log_skips(skips: dict[str, str], prompt_hash: str) -> bool:
    if not skips:
        return True
    stamp = datetime.date.today().isoformat()
    try:
        ws = workspace()
        ws.mkdir(parents=True, exist_ok=True)
        log = ws / "skill-skips.log"
        seen = {tuple(ln.split("\t")[:2]) + (ln.split("\t")[-1],) for ln in log.read_text().splitlines()} if log.exists() else set()
        with log.open("a") as f:
            for skill, reason in skips.items():
                if (stamp, skill, f"p:{prompt_hash}") not in seen:  # a repeated Stop in the same turn logs a skip once
                    f.write(f"{stamp}\t{skill}\t{redact(reason)}\tp:{prompt_hash}\n")
    except OSError:
        return False
    return True


def gate(payload: dict) -> gatekit.Finding | None:
    if not payload.get("transcript_path"):
        raise gatekit.GateError("the Stop payload has no transcript_path")
    unloaded, skips, prompt_hash = check(payload["transcript_path"])
    absent = not_installed(unloaded)
    if absent:
        gatekit.log_decision(GATE, "ignored", "not-installed", gatekit.session_hash(payload))
        unloaded = [s for s in unloaded if s not in absent]
    logged = log_skips(skips, prompt_hash)
    missing = [s for s in unloaded if not (logged and s in skips)]
    if not missing:
        return None
    unlogged = "" if logged else " The skip log could not be written, so a skip-skill line does not count now."
    return "missing-skill", (
        f"SKILL CHECK: the router named {', '.join(missing)} and it is not loaded since the last compaction "
        "(a pre-compaction load is truncated - you are working from memory). Load it with the Skill tool and "
        "redo the answer by its steps, OR if it does not apply write one line in the reply: "
        f"`skip-skill <name>: <why>` (logged to skill-skips.log; a router false positive -> fix its regex).{unlogged}")


def main() -> int:
    return gatekit.run(GATE, gate)


if __name__ == "__main__":
    sys.exit(main())
