#!/usr/bin/env python3
"""Stop hook (blocks): a message draft for a teammate needs the writing skills loaded, and a re-offered draft needs a fresh read of that conversation.

A draft is a ``` fenced block that is not code and either @-mentions someone, opens with a greeting, or has its addressee
(a team name, a DM, a #channel, a thread) in the 200 chars just above it.
AGENT_DRAFT_SKILLS     comma list of skills loaded since the last compaction before any draft (default: humanizer,teammate-message)
AGENT_TEAM_NAMES       regex of teammate names that mark the block below them as a message (default: none)
AGENT_GREETINGS        regex of greeting words a message may open with (default: hey|hi|hello)
AGENT_CHAT_READ_TOOLS  regex of tool names that read the chat; a draft repeated from an earlier reply needs one this turn
                       (default: slack_(read|search); empty = the repeat check is off)
AGENT_REPORT_SKILLS    comma list of skills that write a team report naming people without messaging them; loaded this turn
                       = the gate passes (default: daily-update,standup)
`skip-skill <name>: <why>` in the reply skips one required skill. An invalid regex is a GATE ERROR block.
Repeat blocks, errors and the decision log: see gatekit.py.
"""
from __future__ import annotations
import functools
import json
import os
import re
import sys
from types import SimpleNamespace

GATE = "teammate-draft-check"
try:
    import gatekit
    from transcript_tail import assistant_texts, blocks, is_user_prompt, tail_entries
except Exception as exc:  # a broken install must block, not exit 1 (non-blocking)
    print(json.dumps({"decision": "block", "reason": f"GATE ERROR {GATE}: {exc} - run agentkit doctor"}))
    sys.exit(0)

FENCED = re.compile(r"```(.*?)```", re.S)
CODE_LANGS = {"bash", "sh", "zsh", "shell", "console", "python", "py", "json", "diff", "yaml", "yml", "js", "ts", "sql", "toml"}
MENTION = re.compile(r"@[A-Z][a-z]+")
SKIP = re.compile(r"skip-skill ([a-z0-9-]+): ([^\n]+)")
WHERE = r"\bDM\b|#[a-z][a-z-]+|\bthread\b"


def _names(var: str, default: str) -> list[str]:
    return [s.strip() for s in os.environ.get(var, default).split(",") if s.strip()]


@functools.cache
def _cfg() -> SimpleNamespace:
    names = os.environ.get("AGENT_TEAM_NAMES", "")
    reads = os.environ.get("AGENT_CHAT_READ_TOOLS", r"slack_(read|search)")
    return SimpleNamespace(
        skills=_names("AGENT_DRAFT_SKILLS", "humanizer,teammate-message"),
        reports=set(_names("AGENT_REPORT_SKILLS", "daily-update,standup")),
        addressee=re.compile(rf"(?i)\b(?:{gatekit.env_regex('AGENT_TEAM_NAMES', names).pattern})\b|{WHERE}" if names else f"(?i){WHERE}"),
        greeting=re.compile(rf"(?i)^\s*(?:{gatekit.env_regex('AGENT_GREETINGS', 'hey|hi|hello').pattern})\b"),
        reads=gatekit.env_regex("AGENT_CHAT_READ_TOOLS", reads) if reads else None,
    )


def drafts(text: str) -> list[str]:
    """Teammate message drafts in a reply, whitespace-normalised."""
    cfg, found = _cfg(), []
    for m in FENCED.finditer(text):
        body = m.group(1)
        if body.split("\n", 1)[0].strip().lower() in CODE_LANGS:
            continue
        above = text[max(0, m.start() - 200):m.start()]
        if MENTION.search(body) or cfg.greeting.search(body.lstrip("\n")) or cfg.addressee.search(above):
            found.append(" ".join(body.split()))
    return found


def _turn_start(entries: list[dict]) -> int:
    return max((i for i, e in enumerate(entries) if is_user_prompt(e)), default=-1)


def _tools(entries: list[dict]) -> list[dict]:
    return [b for e in entries for b in blocks(e) if b.get("type") == "tool_use"]


def _loaded(entries: list[dict]) -> set[str]:
    return {str((b.get("input") or {}).get("skill", "")).split(":")[-1] for b in _tools(entries) if b.get("name") == "Skill"}


def missing_skills(entries: list[dict], reply: str) -> list[str]:
    """Required skills not loaded since the last compaction and not skipped, when this turn carries a draft."""
    turn_texts = assistant_texts(entries[_turn_start(entries) + 1:]) + [reply]
    if not any(drafts(t) for t in turn_texts):
        return []
    skipped = {name for t in turn_texts for name, _ in SKIP.findall(t)}
    loaded = _loaded(entries)
    return [s for s in _cfg().skills if s not in loaded and s not in skipped]


def repeated_unread(entries: list[dict], reply: str) -> bool:
    """A draft offered again from an earlier reply with no chat read this turn - it may already be sent or answered."""
    reads = _cfg().reads
    if reads is None:
        return False
    start = _turn_start(entries)
    earlier = {d for t in assistant_texts(entries[:start]) for d in drafts(t)}
    now = [d for t in assistant_texts(entries[start + 1:]) + [reply] for d in drafts(t)]
    return any(d in earlier for d in now) and not any(reads.search(str(b.get("name", ""))) for b in _tools(entries[start + 1:]))


def gate(payload: dict) -> gatekit.Finding | None:
    if not payload.get("transcript_path"):
        raise gatekit.GateError("the Stop payload has no transcript_path")
    entries = tail_entries(payload["transcript_path"], lambda e: e.get("subtype") == "compact_boundary", required=is_user_prompt)
    reply = str(payload.get("last_assistant_message") or "")
    if _loaded(entries[_turn_start(entries) + 1:]) & _cfg().reports:
        return None
    if repeated_unread(entries, reply):
        return "repeated-draft", (
            "REPEATED DRAFT: the reply offers a teammate draft from an earlier reply again without reading that "
            "conversation this turn. Read the DM / channel / thread first - it may already be sent or answered - then rewrite.")
    missing = missing_skills(entries, reply)
    if missing:
        return "draft-without-skill", (
            f"TEAMMATE DRAFT: the reply has a message draft for a teammate but {', '.join(missing)} is not loaded since "
            "the last compaction. Load it, redo the draft by its rules (read that conversation first, match its language "
            "and register), OR write `skip-skill <name>: <why>`.")
    return None


def main() -> int:
    return gatekit.run(GATE, gate)


if __name__ == "__main__":
    sys.exit(main())
