#!/usr/bin/env python3
"""Count tagged misses in <workspace>/misses.md (the board's "Hits" plus new tagged entries) and name the tags that repeat.

Also flags skills skipped 3+ times in <workspace>/skill-skips.log. Run by skill-router.py on a correction, or by hand.
"""
from __future__ import annotations
import re
import sys

from config import workspace

BOARD_ROW = re.compile(r"^\| (\[[a-z-]+\]) \|[^|]*\| (\d+)")
ENTRY_TAG = re.compile(r"^\| \d{4}-\d{2}-\d{2} \| (\[[a-z-]+\])")


def counts(text: str) -> dict[str, int]:
    totals: dict[str, int] = {}
    for line in text.splitlines():
        board = BOARD_ROW.match(line)
        if board:
            totals[board.group(1)] = totals.get(board.group(1), 0) + int(board.group(2))
            continue
        entry = ENTRY_TAG.match(line)
        if entry:
            totals[entry.group(1)] = totals.get(entry.group(1), 0) + 1
    return totals


def skipped(text: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) > 1:
            out[parts[1]] = out.get(parts[1], 0) + 1
    return out


def main() -> int:
    misses = workspace() / "misses.md"
    if misses.exists():
        text = misses.read_text()
        gave_up = workspace() / "improve" / "gave-up.md"
        if gave_up.exists():  # a gate that gave up is a miss of its class too
            text += "\n" + gave_up.read_text()
        repeats = sorted(((n, tag) for tag, n in counts(text).items() if n >= 2), reverse=True)
        if repeats:
            print("MISS REPEATS (misses.md): " + ", ".join(f"{tag} x{n}" for n, tag in repeats)
                  + ". If this correction matches one, its guard failed - propose a structural fix now.")
    log = workspace() / "skill-skips.log"
    if log.exists():
        noisy = sorted(((n, s) for s, n in skipped(log.read_text()).items() if n >= 3), reverse=True)
        if noisy:
            print("SKILL SKIPS (skill-skips.log): " + ", ".join(f"{s} x{n}" for n, s in noisy)
                  + ". Read the reasons: a router false positive -> narrow its regex; a real skip -> why, and a guard.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
