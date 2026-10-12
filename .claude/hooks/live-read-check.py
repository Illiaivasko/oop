#!/usr/bin/env python3
"""Stop hook (blocks): a tracker comment draft needs a live read of that unit THIS turn, and a claimed check needs a Verified record.

A draft is detected by its hand-over shape: a unit link plus a ``` fenced comment in the same reply (see close-out).
AGENT_TRACKER_LINK_RE        regex for a unit link, group 1 = the key (default: .../browse|issues/<KEY>)
AGENT_TRACKER_READ_TOOL      tool-name suffix of the tracker READ tool (empty = this hook is off)
AGENT_TRACKER_SEARCH_TOOL    optional tool-name suffix of a tracker SEARCH tool; a search with comments reads every key it names
AGENT_UNIT_KEY_RE            regex of a bare unit key (default: PROJ-123 shape)
AGENT_DEMO_WORDS             regex of words that mark demo steps just above a fenced block (default: demo|steps)
AGENT_TRACKER_COMMENT_FIELD  word that must appear in that call's arguments to count as "read with comments" (default: comment)
AGENT_RECORDS_SUBDIR         unit records folder inside the workspace (default: tickets)
AGENT_ENV_WORDS              regex of env names a '## Verified' section must name (default: staging|prod|production|local|in-app|demo)
An invalid regex in any of these is a GATE ERROR block. Repeat blocks, errors and the decision log: see gatekit.py.
"""
from __future__ import annotations
import functools
import json
import os
import re
import sys
from types import SimpleNamespace

GATE = "live-read-check"
try:
    import gatekit
    from config import workspace
    from transcript_tail import assistant_texts, blocks, is_user_prompt, tail_entries
except Exception as exc:  # a broken install must block, not exit 1 (non-blocking)
    print(json.dumps({"decision": "block", "reason": f"GATE ERROR {GATE}: {exc} - run agentkit doctor"}))
    sys.exit(0)

READ_TOOL = os.environ.get("AGENT_TRACKER_READ_TOOL", "")
SEARCH_TOOL = os.environ.get("AGENT_TRACKER_SEARCH_TOOL", "")
COMMENT_FIELD = os.environ.get("AGENT_TRACKER_COMMENT_FIELD", "comment")
MENTION = re.compile(r"@[A-Z][a-z]+")
CODE_LANGS = {"bash", "sh", "zsh", "shell", "console", "python", "py", "json", "diff", "yaml", "yml", "js", "ts", "sql", "toml"}
CODE_FENCE = "```"
CLAIMS = re.compile(r"(?i)\b(checked|verified|tested)\b")
FENCED = re.compile(r"```(.*?)```", re.S)


@functools.cache
def _rx() -> SimpleNamespace:
    return SimpleNamespace(
        link=gatekit.env_regex("AGENT_TRACKER_LINK_RE", r"https?://\S+?/(?:browse|issues?)/([A-Za-z][A-Za-z0-9]*-\d+)"),
        key=gatekit.env_regex("AGENT_UNIT_KEY_RE", r"\b[A-Z][A-Z0-9]+-\d+\b"),
        demo=re.compile(r"(?i)(?:" + gatekit.env_regex("AGENT_DEMO_WORDS", "demo|steps").pattern + ")"),
        env=re.compile(r"(?i)\b(" + gatekit.env_regex("AGENT_ENV_WORDS", "staging|prod|production|local|in-app|demo").pattern + r")\b"),
    )


def _current_turn(path: str) -> list[dict]:
    return tail_entries(path, is_user_prompt, required=is_user_prompt)[1:]


def _live_reads(turn: list[dict]) -> set[str]:
    keys = set()
    for entry in turn:
        for b in blocks(entry):
            name = str(b.get("name", ""))
            if b.get("type") != "tool_use" or not (name.endswith(READ_TOOL) or (SEARCH_TOOL and name.endswith(SEARCH_TOOL))):
                continue
            args = json.dumps(b.get("input") or {})
            if COMMENT_FIELD in args or "*all" in args:
                keys.update(k.upper() for k in re.findall(r"[A-Za-z][A-Za-z0-9]*-\d+", args))
    return keys


def _draft_keys(text: str) -> set[str]:
    """Bare keys of a teammate draft (@mention inside) or demo steps (a demo word just above) - a report listing many keys is not one."""
    keys = set()
    for m in FENCED.finditer(text):
        body = m.group(1)
        if body.split("\n", 1)[0].strip().lower() in CODE_LANGS:
            continue
        before = text[max(0, m.start() - 120):m.start()]
        found = set(_rx().key.findall(body))
        if not MENTION.search(body):
            if not _rx().demo.search(before):
                continue
            found |= set(_rx().key.findall(before))
        if len(found) <= 2:
            keys |= found
    return keys


def _drafted(turn: list[dict]) -> set[str]:
    keys = set()
    for text in assistant_texts(turn):
        if CODE_FENCE in text:
            keys |= {k.upper() for k in _rx().link.findall(text)} | {k.upper() for k in _draft_keys(text)}
    return keys


def _claimed(turn: list[dict]) -> set[str]:
    keys = set()
    for text in assistant_texts(turn):
        found = _rx().link.findall(text)
        if CODE_FENCE in text and found and any(CLAIMS.search(block) for block in FENCED.findall(text)):
            keys.update(k.upper() for k in found)
    return keys


def _has_verified_record(key: str) -> bool:
    record = workspace() / os.environ.get("AGENT_RECORDS_SUBDIR", "tickets") / f"{key}.md"
    if not record.exists():
        return False
    section = re.split(r"(?im)^##\s*verified\b", record.read_text(), maxsplit=1)
    if len(section) < 2:
        return False
    return bool(_rx().env.search(re.split(r"(?m)^## ", section[1], maxsplit=1)[0]))


def gate(payload: dict) -> gatekit.Finding | None:
    if not READ_TOOL:
        return None
    if not payload.get("transcript_path"):
        raise gatekit.GateError("the Stop payload has no transcript_path")
    turn = _current_turn(payload["transcript_path"])
    if payload.get("last_assistant_message"):
        # the final reply may not be in the transcript yet when Stop fires
        turn.append({"type": "assistant", "message": {"content": [{"type": "text", "text": str(payload["last_assistant_message"])}]}})
    missing = sorted(_drafted(turn) - _live_reads(turn))
    if missing:
        return "unread-draft", (
            f"LIVE-READ CHECK: a comment draft for {', '.join(missing)} was written without reading the live unit "
            f"this turn. Read each one with its comments ({READ_TOOL}), reconcile (already posted? new asks? "
            "status?), then rewrite the answer.")
    unproven = sorted(k for k in _claimed(turn) if not _has_verified_record(k))
    if unproven:
        return "unverified-claim", (
            f"VERIFIED CHECK: the comment for {', '.join(unproven)} claims a check, but its unit record has no "
            "'## Verified' section naming the env and what was checked against each acceptance point. Map every "
            "point to its evidence (the human's run, a test, a probe), write the section, then give the comment "
            "- or drop the claim from it.")
    return None


def main() -> int:
    return gatekit.run(GATE, gate)


if __name__ == "__main__":
    sys.exit(main())
