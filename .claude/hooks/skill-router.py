#!/usr/bin/env python3
"""UserPromptSubmit hook: print the task protocol + the SPECIFIC skills the prompt's wording calls for.

A generic "find the skill" nudge gets skipped when the procedure feels familiar; naming the skill does not.
Unit keys are matched on the prompt as typed:
AGENT_UNIT_KEY_PREFIXES  ','-separated key prefixes (e.g. PROJ,OPS); keys then match in any case (proj-12 -> PROJ-12)
AGENT_UNIT_KEY_RE        else this regex (default: 2+ capitals, a dash, digits - so gpt-4 / python-3 / utf-8 are not keys)
A missing routes.json or an invalid regex prints a GATE ERROR line after the protocol instead of crashing.
"""
from __future__ import annotations
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

PROTOCOL = ("TASK PROTOCOL: if this is a substantive task (fix / investigation / ticket / flow change) invoke "
            "task-protocol -> recall memory by concrete key -> find-skills and load the matching skill(s) -> "
            "open/append .work/tickets/<KEY>.md and record WHAT / WHERE(file:line) / WHY + dead-ends AS YOU GO. "
            "Skip only for a trivial one-off lookup.")


# The lead pointing out a miss. Template: add the phrases your lead actually uses, in every language they use.
CORRECTION = re.compile(r"а чому ти|чому ти (не|про це)|ти (ж )?(не|забув)|не той формат|знову (те саме|ти|не)|я ж (казав|просив)|why didn.t you|you (forgot|missed)|not the right format|(same|that) (mistake|thing|error) again|you did (it|that) again|i told you")
BIG_TASK = re.compile(r"архітектур|спроєкту|продума|нов\w* (фіч|модул|сервіс|систем)|оцін\w*|architecture|estimate|\bdesign\b|research|integration|new (module|service)|\bepic\b")
DEFAULT_UNIT_KEY = r"\b[A-Z][A-Z0-9]*[A-Z][A-Z0-9]*-\d+\b"
FEEDBACK = ("FEEDBACK: the lead is pointing out a miss. 1) Answer WHY plainly, fix it. 2) Append a tagged line to "
            "misses.md in the workspace (tags in its Repeat board). 3) If the tag already has hits, propose a STRUCTURAL "
            "guard (hook / test / skill gate) in the same reply - not another sentence in a rule. 4) A stated preference "
            "-> the matching skill (updating-skills) or a memory.")
BIG = ("BIG TASK: before designing, find-skills step 0 - search installed skills, then obra/superpowers / "
       "anthropics/skills / web for a skill on this domain; adapt one (new-skill) or note 'none found' in the record.")


def load_routes() -> list[tuple[str, str]]:
    """Generated from routing.yaml by `agentkit render` - edit routing.yaml, never routes.json."""
    return [(" + ".join(r["skills"]), "|".join(r["triggers"])) for r in json.loads((HERE / "routes.json").read_text())]


def unit_key_re() -> re.Pattern:
    prefixes = [p.strip() for p in os.environ.get("AGENT_UNIT_KEY_PREFIXES", "").split(",") if p.strip()]
    if prefixes:
        return re.compile(r"\b(?:" + "|".join(map(re.escape, prefixes)) + r")-\d+\b", re.I)
    from config import env
    return re.compile(env("AGENT_UNIT_KEY_RE") or DEFAULT_UNIT_KEY)


def unit_keys(prompt: str) -> list[str]:
    return sorted({m.group(0).upper() for m in unit_key_re().finditer(prompt)})


def _run(script: str, *args: str) -> str:
    try:
        out = subprocess.run([sys.executable, str(HERE / script), *args], capture_output=True, text=True, timeout=5)
        return out.stdout.strip()
    except Exception:
        return ""


def _extras(prompt: str, keys: list[str]) -> None:
    if CORRECTION.search(prompt):
        print(FEEDBACK)
        repeats = _run("misses-check.py")
        if repeats:
            print(repeats)
    if BIG_TASK.search(prompt):
        print(BIG)
    for key in keys[:3]:
        recalled = _run("kb/recall.py", key)
        if recalled:
            print("\n".join(recalled.splitlines()[:8]))
        print(f"LIVE {key}: re-read it (with comments) before any status, demo or comment.")


def main() -> int:
    try:
        typed = json.load(sys.stdin).get("prompt") or ""
        # route on what the lead typed, not on logs / commit lists they pasted in
        typed = re.sub(r"<pasted_content[^>]*>.*?</pasted_content[^>]*>", " ", str(typed), flags=re.S | re.I)
    except Exception:
        typed = ""
    prompt = typed.lower()
    # a subagent hand-back or task notification is not the lead's request - routing on it only adds noise
    if "[subagent hand-back]" in prompt or "<task-notification>" in prompt:
        print(PROTOCOL)
        return 0
    print(PROTOCOL)
    try:
        routes = load_routes()
        keys = unit_keys(typed)
    except (OSError, ValueError, KeyError, TypeError, re.error) as exc:
        print(f"GATE ERROR skill-router: {type(exc).__name__}: {exc} - run agentkit render / agentkit doctor. "
              "No skill was routed for this prompt: find-skills by hand.")
        return 0
    hits = [skill for skill, rx in routes if re.search(rx, prompt)]
    if hits:
        print("SKILL ROUTER: this prompt matches -> LOAD NOW, before acting: " + "; ".join(hits) + ".")
    _extras(prompt, keys)
    return 0


if __name__ == "__main__":
    sys.exit(main())
