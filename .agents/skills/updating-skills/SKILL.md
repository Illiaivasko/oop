---
name: updating-skills
description: Use when a skill itself needs editing - the human corrected how it works or what its output looks like, its example went stale, its procedure changed, or it failed to trigger when it should have.
---
Adapted from: obra/superpowers writing-skills (refactor cycle) + our lessons (a corrected output was fixed once but the skill kept producing the old one; a new rule was stacked next to the rule it replaced).

**Core rule:** fix the SKILL, not just the one-off output - so the next run follows the new way.

## Steps
1. Read the whole SKILL.md first.
2. Reword or replace the rule that was overridden. NEVER stack a new rule next to the old one it contradicts.
3. If the OUTPUT was corrected, replace the example with the latest REAL approved output - never an invented one. The example must itself obey the rules (a "be short" skill needs a short example).
4. Did not trigger? Fix the `description` (add the words actually used) and the router entry in `hooks/skill-router.py`; test with the prompt that missed.
5. Keep frontmatter intact; the description stays triggers-only, never the steps.
6. Match the house style: terse, imperative, one line per rule. Keep the `LIVING:` line.
7. Log it: one line in `misses.md` if a miss triggered the edit.

## Quick reference
| Signal | Edit |
|---|---|
| "Not like that, like this" | rule + example |
| Skill not loaded when it should be | description + router |
| Step order wrong / missing | the phase list |
| Example no longer true | replace with a real current one |

## Don'ts
- Don't change always-on project rules (the instructions file) from here - propose the exact text and agree it with the human first.
- Don't leave an example that contradicts the updated rules.
- Don't create a new skill for a one-off (`new-skill` decides).

## Example
Human: "the status comment is too long, write it like mine". Replaced the format rule with "3 short sentences: where it is, what changed, the control" and swapped the example for the comment they had actually posted.

LIVING: update if the skill layout, frontmatter fields or house style change.
