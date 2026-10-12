#!/usr/bin/env python3
"""Antigravity Stop Hook:
Advisory check when model stops: if code files were modified more recently than
.work/session_state.md, injects a reminder to record before stopping.
"""

import json
import os
import pathlib
import sys


def find_workspace(payload: dict) -> pathlib.Path:
    paths = payload.get("workspacePaths", [])
    if paths:
        candidate = pathlib.Path(paths[0])
        if candidate.exists():
            return candidate
    return pathlib.Path(os.getcwd())


def newest_code_mtime(ws: pathlib.Path) -> float:
    newest = 0.0
    skip_parts = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".work"}
    globs = ["*.py", "*.ts", "*.tsx", "*.js", "*.go", "*.rs"]
    for pattern in globs:
        for f in ws.rglob(pattern):
            if any(part in f.parts for part in skip_parts):
                continue
            try:
                newest = max(newest, f.stat().st_mtime)
            except OSError:
                continue
    return newest


def main() -> None:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}

    ws = find_workspace(payload)
    state_file = ws / ".work" / "session_state.md"

    if state_file.exists():
        try:
            state_mtime = state_file.stat().st_mtime
            code_mtime = newest_code_mtime(ws)
            if code_mtime > state_mtime + 60:
                output = {
                    "injectSteps": [
                        {
                            "ephemeralMessage": "RECORD CHECK: Code files changed more recently than .work/session_state.md. "
                                               "Please refresh .work/session_state.md (Focus, Next action, Recent commits) "
                                               "and update .work/tickets/<TASK>.md before completing."
                        }
                    ]
                }
                print(json.dumps(output))
                return
        except Exception:
            pass

    print(json.dumps({}))


if __name__ == "__main__":
    main()
