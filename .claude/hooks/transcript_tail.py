"""Read only the end of a (large) session transcript: entries back to the last one that matches a predicate.

The file is read backwards in fixed chunks and each line is parsed once, so time and memory follow the tail, not the file.
Tool-result entries (the bulk of a transcript's bytes) are skipped before parsing: no gate reads them.
Reading normally stops at MAX_BYTES. With `required` (e.g. the turn start) it goes on to AGENT_TRANSCRIPT_CAP_MB
(default 512) until a required entry is seen, and raises TurnTooLong if the cap is hit first - never a silent partial read.
"""
from __future__ import annotations
import json
import os
import re
from collections.abc import Callable, Iterator

CHUNK = 1024 * 1024
MAX_BYTES = 96 * 1024 * 1024
DEFAULT_CAP_MB = 512
TOOL_RESULT = re.compile(rb'"type":\s*"tool_result"')


def _parse(line: bytes) -> dict | None:
    if not line.strip() or TOOL_RESULT.search(line):
        return None
    try:
        entry = json.loads(line)
    except ValueError:
        return None
    return entry if isinstance(entry, dict) else None


class TurnTooLong(Exception):
    pass


def hard_cap() -> int:
    from config import env
    raw = env("AGENT_TRANSCRIPT_CAP_MB") or str(DEFAULT_CAP_MB)
    try:
        mb = int(raw)
    except ValueError as exc:
        raise ValueError(f"AGENT_TRANSCRIPT_CAP_MB is not a whole number of MB: {raw!r}") from exc
    if mb <= 0:
        raise ValueError(f"AGENT_TRANSCRIPT_CAP_MB must be positive: {raw!r}")
    return mb * 1024 * 1024


def _lines_backwards(path: str, limit: int) -> Iterator[tuple[bytes, int]]:
    """(complete line, bytes read so far) from the end of the file back to `limit` bytes, last line first."""
    size = os.path.getsize(path)
    stop = max(0, size - limit)
    pos, carry = size, b""
    with open(path, "rb") as f:
        while pos > stop:
            step = min(CHUNK, pos - stop)
            pos -= step
            f.seek(pos)
            parts = (f.read(step) + carry).split(b"\n")
            carry = parts.pop(0) if pos > 0 else b""
            for line in reversed(parts):
                yield line, size - pos


def tail_entries(path: str, until: Callable[[dict], bool], required: Callable[[dict], bool] | None = None) -> list[dict]:
    """Entries back to the last one matching `until` and, if given, at least back to the last one matching `required`.

    No `until` match: everything read (up to MAX_BYTES). No `required` match within the hard cap: TurnTooLong.
    """
    limit = hard_cap() if required else MAX_BYTES
    found: list[dict] = []
    need, read, at_start = required is not None, 0, True
    for line, read in _lines_backwards(path, limit):
        if not need and read > MAX_BYTES:
            break
        entry = _parse(line)
        if entry is None:
            continue
        found.append(entry)
        if need and required(entry):
            need = False
        if until(entry) and not need:
            break
    else:
        at_start = read >= os.path.getsize(path)
    if need and not at_start:
        raise TurnTooLong(f"turn too long to verify: its start is more than {limit // (1024 * 1024)} MB back in the "
                          "transcript (AGENT_TRANSCRIPT_CAP_MB)")
    found.reverse()
    return found


def blocks(entry: dict) -> list:
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []


def is_user_prompt(entry: dict) -> bool:
    if entry.get("type") != "user" or entry.get("isMeta"):
        return False
    return any(b.get("type") == "text" for b in blocks(entry))


def assistant_texts(turn: list[dict]) -> list[str]:
    return [str(b.get("text", "")) for e in turn if e.get("type") == "assistant"
            for b in blocks(e) if b.get("type") == "text"]


def final_reply(path: str) -> str:
    """The last reply of the current turn: the assistant text after the turn's last tool call."""
    texts: list[str] = []
    for entry in reversed(tail_entries(path, is_user_prompt)[1:]):
        if entry.get("type") != "assistant":
            continue
        entry_blocks = blocks(entry)
        if any(b.get("type") == "tool_use" for b in entry_blocks):
            break
        texts += [str(b.get("text", "")) for b in reversed(entry_blocks) if b.get("type") == "text"]
    return "\n".join(reversed(texts))
