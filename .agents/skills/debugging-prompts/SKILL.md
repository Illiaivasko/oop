---
name: debugging-prompts
description: A model gives the wrong label, wrong tool arguments or a wrong reply and the cause may be prompt text - a classifier picks the wrong intent, "the prompt doesn't obey", "the model ignores the rule", "debug the prompt" - or before any prompt edit that has to be proven, or when a prompt problem looks structural (every edit moves other phrases). Says how to find the cause in the prompt and prove a fix with measured runs.
---
Adapted from Anthropic's prompt-audit guide (claude-api skill, `shared/prompt-audit.md`), Anthropic's "Define success criteria and build evaluations" and "Prompting best practices" (examples steer hardest), and Hamel Husain's error analysis (notes -> failure modes -> counts).

**Core rule: a prompt edit is a hypothesis. It counts only when the failing case passes AND the untouched panels did not move, measured N times in one window against the unchanged prompt.**

## 1. Real failures first
Collect failing turns (test failures, user reports, log lines with their context). One plain note each, group them into failure modes, count, fix the biggest. Which model made the mistake (a classifier, a tool router, the reply writer)? Read its RAW output - the extracted params, the tool-call input - not the screen it led to.

## 2. Inventory every rule that touches it
Dump the full assembled prompt, search every trigger word of the bad phrase, list each hit as file:line -> the label it pushes. Look for: the same words under two labels; an example contradicting a rule (models copy examples over rules); a context condition placed away from the examples it governs; one rule repeated with different wording. Search tests and log parsers for the text before changing it.

## 3. One hypothesis, the smallest edit
"X gets Y because example A and line B say Y, and gate C sits after them." Change only that: put the context on the example, name the exact output in the gate, align or delete the contradicting copy. Never stack a counter-rule on a conflict. Never copy a test phrase into the prompt - measure paraphrases.

## 4. Measure - the gate
- One branch per variant; `<PROMPT_EVAL_HARNESS>` runs the REAL call of every arm at once, with panels: the target in the wrong context AND where the old label is right, first-turn border cases, everyday controls. Report hits/N with a confidence interval and every control whose majority moved.
- N = 20 per target / border phrase, 5 per control. If production caches the first answer per process, a phrase that is right 14/20 is wrong for 30% of processes: judge hits/N, never the majority.
- Pass: the target fails on the old prompt and passes on the variant; anchors (>= 19/20 before) lose at most 1; no control majority moves. Anything moved -> back to step 3, never a second edit on top.
- Then a regression test or scenario, a live run with a control, and the lead sees the table before a shared prompt change lands.

## Structure is the cause -> plan, don't patch
When every edit of one big shared prompt moves unrelated phrases, the fix is structural: small modules with context loaded by STRUCTURED state, so each call reads less and rules collide less. That is a feature to design and plan, never something to start inside a bug fix. Until then, prefer context gated by state (the first answer + what is on screen) over editing the shared prompt; never select by message text.

## Red flags
| Thought | Reality |
|---|---|
| "Two lines, no need to measure" | Small edits of a big prompt move unrelated borderline phrases |
| "3/3 by hand" | Borderline labels flip at N=20 |
| "Add NEVER <wrong label> here" | That rule usually exists; the conflicting example wins |
| "A code guard is enough" | Only if a structural signal separates the cases |
| "Cache the fallback, it's rare" | A cached fallback repeats for every user until restart |

## Example
A list-paging phrase ("show me different ones" on a results list) was labelled as "go back" -> dead end. Five edits of the shared prompt fixed it but each moved unrelated first-turn phrases (one from 19/20 to 2/20). A note added on every list turn fixed it but flipped a filter phrase. Asking again with the note ONLY when the first answer was "go back" on a list: target 92 -> 218/220, nothing else moved, extra latency only on those turns - and the unsettled fallback is never cached.

LIVING: add each measured edit (variant, panels, result) to the example.
