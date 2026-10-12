#!/usr/bin/env python3
"""Antigravity PreInvocation Hook:
1. Injects live session state (.work/session_state.md) into model context.
2. Injects skill routing based on user prompt.
3. Enforces history recording and proactive skill creation rules.
"""

import json
import os
import pathlib
import re
import sys

ROUTES = [
    ("close-out", r"закри|close|closing|\btesting\b|\bdone\b|перевест|статус|коментар (до|в) тікет|jira comment"),
    ("teammate-message", r"меседж|повідомлен|напиш\w* .{0,20}(груп|слак)|slack|reply to|відповід\w* (йому|їм)"),
    ("standup", r"стендап|standup|stand-up"),
    ("daily-update", r"дейлі|\bdaily\b|апдейт за сьогодні|end of day"),
    ("mr-description", r"мердж|merge request|\bmr\b|опис до мерж"),
    ("updating-skills", r"(поправ|онов|зміни|виправ|update|fix)\w* (\w+ )?скіл|скіл\w* (поправ|онов)|update (the )?skill"),
    ("debugging-prompts", r"промт|\bprompt\b|класифікатор|classifier|подебаж"),
    ("explaining-decisions + status-update", r"поясн\w* (рішен|чому)|чому ти (так|це|вирішив|вибрав)|що ти (вирішив|вибрав)|в курсі|decision|why did you"),
    ("new-skill", r"\bнов\w* скіл|створ\w* скіл|зроб\w* скіл|new[_ -]?skill|create a skill"),
    ("update-graph", r"\bграф|зв.язк|лінк|orphan|\bgraph\b"),
    ("ticket-pipeline", r"worktree|work ?tree|(ворк|вокр) ?тр|паралельн\w* (таск|тікет|фікс)|кілька (таск|тікет)|батч|batch of (tickets|fixes)|закри\w* (всі|все)"),
    ("delegate-to-subagents", r"суб ?агент|subagent|делегу|паралельно|parallel agents"),
    ("investigate-task", r"досліди|розберись|відтворю|чому так|how bad|наскільки|audit|аудит|is it real"),
    ("build-a-feature + risk-check + writing-code", r"фі+ч|додай|зроби щоб|feature|implement|new step"),
    ("fix-a-bug + risk-check + writing-code", r"\bбаг(и|у|ом|ів)?\b|не працює|broken|фікс|поправ(?!\w* (\w+ )?скіл)|виправ(?!\w* (\w+ )?скіл)|\bfix\b|рефактор|refactor"),
    ("verification-before-completion", r"протест|перевір\w* (локально|на staging)|verify|demo|демо"),
]


def find_workspace(payload: dict) -> pathlib.Path:
    paths = payload.get("workspacePaths", [])
    if paths:
        candidate = pathlib.Path(paths[0])
        if candidate.exists():
            return candidate
    return pathlib.Path(os.getcwd())


def get_latest_user_prompt(transcript_path: str | None) -> str:
    if not transcript_path or not os.path.exists(transcript_path):
        return ""
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in reversed(f.readlines()):
                try:
                    step = json.loads(line)
                    if step.get("type") == "USER_INPUT":
                        return str(step.get("content", ""))
                except Exception:
                    continue
    except Exception:
        pass
    return ""


def main() -> None:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}

    ws = find_workspace(payload)
    state_file = ws / ".work" / "session_state.md"

    context_parts = []

    # 1. State snapshot
    if state_file.exists():
        try:
            lines = state_file.read_text(encoding="utf-8").splitlines()
            top_block = "\n".join(lines[:45])
            context_parts.append(f"=== CURRENT WORKSPACE STATE (.work/session_state.md) ===\n{top_block}")
        except Exception:
            pass

    # 2. Skill Router
    prompt = get_latest_user_prompt(payload.get("transcriptPath"))
    if prompt:
        p_lower = prompt.lower()
        hits = [skill for skill, rx in ROUTES if re.search(rx, p_lower)]
        if hits:
            context_parts.append(f"=== SKILL ROUTER ===\nThis prompt matches -> LOAD NOW, before acting: {'; '.join(hits)}.")

    # 3. Dynamic Adaptation & Memory Mandate
    context_parts.append("""=== HARNESS OPERATING MANDATE ===
1. PERSISTENCE & HISTORY:
   - Maintain .work/session_state.md: update Focus, Next action, Recent commits, and Open findings.
   - For every task, keep/update a unit file under .work/tickets/<TASK_ID>.md.
   - Never finish a substantive task without updating .work/session_state.md.
2. DYNAMIC SKILL CREATION & ADAPTATION:
   - Do NOT leave valuable domain procedures in temporary chat history.
   - When you discover, refine, or stabilize a multi-step workflow, or when the user teaches you project requirements:
     PROACTIVELY CREATE OR UPDATE A SKILL in .agents/skills/<skill-name>/SKILL.md (YAML frontmatter: name, description).
   - When a mistake occurs, record it in .work/misses.md with a preventative guard rule.""")

    output = {
        "injectSteps": [
            {
                "ephemeralMessage": "\n\n".join(context_parts)
            }
        ]
    }

    sys.stdout.write(json.dumps(output))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
