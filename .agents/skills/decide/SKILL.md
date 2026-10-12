---
name: decide
description: Use when the human is choosing between options and wants a reasoned pick, not two lists - tools, vendors, offers, approaches, plans - "help me decide", "which should I pick", "A or B", "compare the options", "pros and cons", "weigh the options", "decision matrix", "допоможи вибрати", "що краще", "що обрати", "порівняй варіанти", "плюси і мінуси", "зваж варіанти". Gives a reasoned pick with its confidence. Not for explaining a decision already made (explaining-decisions) or stress-testing one (challenge).
---
Adapted from https://github.com/mohitagw15856/pm-claude-skills@d3897cee0eed skills/decision-helper (MIT) - see NOTICE.

**Core rule: criteria before options, then commit to a lean.** Name what a good outcome depends on and weigh it BEFORE scoring the options; end with a recommendation and its confidence, never "it depends" without saying on what.

## When
- 2+ concrete options and a choice to make, the human's or one the agent must recommend.
- Not: explaining or logging a decision (`explaining-decisions` - this skill hands off to it). Not: attacking a choice already made (`challenge`). Missing facts about the options -> get them first (`deep-research`, or `verify-claims` for a specific claim).

## Steps
1. **Frame.** The options (2+, concrete), hard constraints (deal-breakers filter options out BEFORE scoring), and reversibility: one-way door (hard to undo) or two-way (cheap to undo). A two-way door deserves a quick pass; a one-way door deserves the full one.
2. **Criteria first.** List what a good outcome depends on, from what the human cares about. If they have not said, propose 3-6 and ask them to weight them. Weights are honest: if cost matters 3x more than speed, say so - equal weights are a hidden choice.
3. **Facts per option.** Each fact a score rests on carries its source (URL + date seen, a file, the human's own words), or is marked `[unverified]` / *(assumed - confirm)*. No invented numbers.
4. **Score.** Each option x each criterion. Use ranges or low/medium/high where you cannot know exactly - no false precision. Show the weighted total, and say where a "close call" is not close.
5. **Lean.** The recommended option + confidence (high / medium / low) + why in one or two lines.
6. **Tiebreaker.** The single unknown that would flip the answer, and how to find it out cheaply.
7. **Gut-check.** Ask: does the winner sit right? Unease is a criterion nobody named yet - add it and re-score if so.
8. **Hand off.** The decision is written up and owned through `explaining-decisions`: its six-line shape, who decides (the human's call vs the agent's two-way door), the decision log. If the comparison goes to other people, it goes through `humanizer`. Never act on a one-way decision that belongs to the human before they answer.

## Output template
```markdown
## Deciding: <A> vs <B> [vs <C>] | reversibility: one-way / two-way
Constraints applied: <what was filtered out and why>

| Criterion | Weight | A | B | Source / basis |
|---|---|---|---|---|
| <criterion> | high/med/low or 1-3 | <score or range> | <score or range> | [n] / human / assumed |
| **Weighted** | | <total> | <total> | |

**Lean:** <option> - confidence <level>. Why: <1-2 lines>
**Tiebreaker:** <the unknown that flips it> - find out by: <cheap check>
**Gut-check:** does <option> sit right? If not, what is missing?
Sources: [n] <locator, date>
```
Then the `explaining-decisions` block when the human decides or the agent acted.

## Red flags
| Thought | Reality |
|---|---|
| "Both have merits" | The human came to avoid exactly this - lean, with confidence |
| "Score = 7.4" for something unknowable | Ranges and labels, not false precision |
| Criteria chosen after looking at the options | Rationalising a favourite - criteria first |
| Equal weights by default | A hidden choice; ask or justify |
| A price or spec from memory | Source it or mark it `[unverified]` |
| "I'll just go with the winner" on a one-way door | Explain and wait for the human |

## Example
Three note apps for a small team. Constraint: must export to plain Markdown (one option dropped). Criteria: export fidelity (high), cost (medium), sharing (medium), learning curve (low). Prices and export behaviour sourced from each vendor's docs with dates. Lean: option B, medium confidence. Tiebreaker: does B keep links on export - test with one folder. Handed to `explaining-decisions` as "who decides: you".

LIVING: when a lean turned out wrong, add the missed criterion pattern to step 2.
