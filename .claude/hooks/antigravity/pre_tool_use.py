#!/usr/bin/env python3
"""Antigravity PreToolUse Hook:
Intercepts run_command tool calls.
If command contains 'git commit', checks for:
1. Secret files staged (.env, .pem, .key, credentials.json, sqlite3)
2. Staged temporary debug lines (print(, console.log(, debugger;, pdb, # TEMP)
Blocks tool execution with 'decision': 'deny' if violations exist.
"""

import json
import os
import pathlib
import subprocess
import sys


def find_workspace(payload: dict) -> pathlib.Path:
    paths = payload.get("workspacePaths", [])
    if paths:
        candidate = pathlib.Path(paths[0])
        if candidate.exists():
            return candidate
    return pathlib.Path(os.getcwd())


def main() -> None:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}

    tool_call = payload.get("toolCall", {})
    name = tool_call.get("name", "")
    args = tool_call.get("args", {})
    cmd = args.get("CommandLine", "")

    if "git commit" not in cmd:
        print(json.dumps({"decision": "allow"}))
        return

    ws = find_workspace(payload)

    # 1. Check for secret files in staged files
    try:
        staged_files = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=str(ws),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()

        secret_patterns = [".env", ".pem", ".key", "id_rsa", "credentials.json", ".sqlite3", "_token.txt"]
        bad_files = [f for f in staged_files if any(p in f.lower() for p in secret_patterns)]
        if bad_files:
            print(json.dumps({
                "decision": "deny",
                "reason": f"COMMIT BLOCKED: Attempting to commit secret/credential/database files: {', '.join(bad_files)}"
            }))
            return
    except Exception:
        pass

    # 2. Check for temporary debug lines in added code lines
    try:
        diff_out = subprocess.run(
            ["git", "diff", "--cached", "-U0", "--", ".", ":(exclude)*.md", ":(exclude)*.txt", ":(exclude)*.json", ":(exclude)*hooks*", ":(exclude)*scaffold*", ":(exclude)*setup*"],
            cwd=str(ws),
            capture_output=True,
            text=True,
        ).stdout

        debug_patterns = [
            "breakpoint()",
            "import pdb",
            "pdb.set_trace",
            "console.log(",
            "debugger;",
            "# TEMP",
            "# DEBUG",
            "TEMP_LOG",
        ]

        violations = []
        for line in diff_out.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                if any(p in line for p in debug_patterns):
                    violations.append(line)

        if violations and "--no-verify" not in cmd:
            print(json.dumps({
                "decision": "deny",
                "reason": f"COMMIT BLOCKED: Temporary debug statements detected in staged diff:\n" + "\n".join(violations[:5])
            }))
            return
    except Exception:
        pass

    print(json.dumps({"decision": "allow"}))


if __name__ == "__main__":
    main()
