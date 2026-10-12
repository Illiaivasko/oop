---
name: new-skill
description: Use when about to create a new skill, or substantially rewrite a general-process one ("new skill", "make a skill for X", "write a skill"). Finds an established skill to adapt before anything is written from scratch.
---
Adapted from: obra/superpowers writing-skills + Anthropic skill-creator + our lessons (general-process skills written from scratch, with descriptions that narrated the steps - the agent followed the description and skipped the body).

**Rule:** general-process skills (debugging, review, delegation, planning, verification, skill-writing) are ADAPTED from a proven source. Only project-specific skills (a team's message format, a project's routes) are written from the project's own examples.

## 1. Search first
1. Skills already installed in this session.
2. obra/superpowers: `raw.githubusercontent.com/obra/superpowers/main/skills/<name>/SKILL.md`.
3. anthropics/skills (e.g. skill-creator), then a web search.
Read candidates IN FULL, not a README summary.

## 2. Adapt, do not paste
Keep their core rule, phases, red flags and rationalization tables. Add YOUR lessons from `misses.md` - that is what the source lacks. Drop what conflicts with your project rules. First body line: `Adapted from: <source> + <our lessons>`.

## 3. Write it right
- `description` = WHEN to load: trigger situations + the words people actually type (every language they use) + what it does in a few words. NEVER the steps. Slightly pushy - under-triggering is the common failure.
- Body: core rule first; short phases; a quick-reference table; red flags / rationalizations; ONE example. Under ~500 words; link siblings by name instead of repeating them.
- Hard words for hard rules (MUST / NEVER), not "prefer / consider".
- End with a `LIVING:` line.

## 4. Test it
- Discipline skill: run one scenario WITHOUT the skill, note how it goes wrong; then WITH it; plug each new rationalization and re-test.
- Trigger: pipe 3 real past prompts through `hooks/skill-router.py`; add near-miss prompts that must NOT trigger.

## 5. Wire it
Row in `find-skills`; trigger words in `hooks/skill-router.py` ROUTES; a link from the hub it belongs to (`writing-code`, `task-protocol`); a general lesson -> `AGENT_PLAYBOOK.md`; a line in `process_improvement_plan.md`.

## Red flags
A general skill written from memory; a description that narrates the procedure; no example; not wired into the index and router; a skill for a one-off.

## Example
Needed a "handle review feedback" skill: found superpowers receiving-code-review, kept its response pattern and forbidden-phrases table, added our miss (a blind fix broke a healthy path -> `risk-check` after implementing), description rewritten to triggers only, router entry added and tested with three past prompts.

LIVING: add a good new source to step 1 when one is found.
