#!/usr/bin/env python3
"""Stop hook (advisory, never blocks): nudge to record when code changed more recently than the state file."""
from __future__ import annotations
import json
import sys

from config import code_dirs, code_globs, state_file, workspace

GRACE_SECONDS = 90
SKIP_PARTS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}


def newest_code_mtime() -> float:
    newest = 0.0
    ws = workspace().resolve()
    for d in code_dirs():
        if not d.exists():
            continue
        for pattern in code_globs():
            for f in d.rglob(pattern):
                if SKIP_PARTS & set(f.parts) or ws in f.resolve().parents:
                    continue
                try:
                    newest = max(newest, f.stat().st_mtime)
                except OSError:
                    continue
    return newest


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("stop_hook_active"):
        return 0
    state = state_file()
    if not state.exists():
        return 0
    if newest_code_mtime() > state.stat().st_mtime + GRACE_SECONDS:
        print(f"RECORD CHECK: code changed more recently than {state.name}. Refresh it and the unit record "
              "(what / where file:line / why + dead ends) before ending.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
