#!/usr/bin/env python3
"""Stop hook (advisory, never blocks): nudge when recently edited notes are unlinked, or code outran the module notes.

AGENT_NOTES_SUBDIR  module-notes folder inside the workspace (default: architecture)
"""
from __future__ import annotations
import json
import os
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "kb"))
from config import code_dirs, code_globs, workspace  # noqa: E402
from kb import graph, is_artifact  # noqa: E402

RECENT_SECONDS = 6 * 3600
GRACE_SECONDS = 90


def _newest(paths) -> float:
    return max((p.stat().st_mtime for p in paths), default=0.0)


def graph_gaps(since: float) -> list[str]:
    primary, back, broken = graph()
    out = [f"orphan: {nid}" for nid, (path, links) in primary.items()
           if path.stat().st_mtime >= since and not is_artifact(path) and not links and not back[nid]]
    out += [f"broken: {src} -> [[{dst}]]" for src, dst in broken if primary[src][0].stat().st_mtime >= since]
    return out


def notes_behind() -> bool:
    notes = workspace() / os.environ.get("AGENT_NOTES_SUBDIR", "architecture")
    if not notes.exists():
        return False
    code = [f for d in code_dirs() if d.exists() for g in code_globs() for f in d.rglob(g)
            if workspace().resolve() not in f.resolve().parents]
    return _newest(code) > _newest(notes.glob("*.md")) + GRACE_SECONDS


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("stop_hook_active"):
        return 0
    gaps = graph_gaps(time.time() - RECENT_SECONDS)
    if gaps:
        print("GRAPH CHECK: recently edited notes need links (update-graph skill): " + "; ".join(gaps[:8]))
    if notes_behind():
        print("GRAPH CHECK: code changed after the newest module note - add what you learned to its "
              "'## Learned' section (update-graph skill).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
