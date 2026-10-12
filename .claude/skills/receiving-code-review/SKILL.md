---
name: receiving-code-review
description: Use when code review feedback arrives - from a human, a reviewer agent or a tool - before implementing any suggestion, especially when an item is unclear, seems wrong for this codebase, or conflicts with an earlier decision.
---
Adapted from: obra/superpowers receiving-code-review + our lessons (a suggestion was applied blind and broke a healthy path; feedback was acknowledged with filler instead of a fix).
Adapted from https://github.com/obra/superpowers (MIT) - see NOTICE.

**Core rule:** verify before implementing, ask before assuming, technical correctness over social comfort.

## Response pattern
1. READ all feedback before reacting.
2. UNDERSTAND: restate each item in your own words, or ask.
3. VERIFY against the codebase: is it true here? what does it break? why is the current code this way?
4. EVALUATE: sound for THIS codebase and its constraints?
5. RESPOND: a technical acknowledgment or reasoned pushback.
6. IMPLEMENT one item at a time, test each, then `risk-check` on the whole.

## Rules
- Any item unclear -> STOP, ask about those items BEFORE implementing any. Items are often related.
- Feedback conflicts with a decision the human made -> raise it with the human, do not silently pick.
- A "do it properly" suggestion -> grep for real usage first; unused -> propose removing it (YAGNI).
- Cannot verify -> say so: "I can't verify X without Y - investigate, ask, or proceed?"
- Order: blocking (breaks, security) -> simple -> complex.

## How to answer
| Do | Don't |
|---|---|
| "Fixed - <what changed, where>." | "Great point!" / "You're absolutely right!" |
| "Checked: <fact>. Keeping it because <reason>." | Defend without evidence |
| "You were right - <fact>. Fixing." | A long apology |
| Just fix it and show the diff | Thanks and filler |

## When to push back
It breaks existing behaviour; the reviewer lacks context; it violates YAGNI; it is wrong for this stack; it conflicts with an agreed design. Use code, tests or a live control as the argument.

## Example
Reviewer: "remove the legacy branch". Checked: a supported client version still sends the old field. Reply: "Keeping it - clients below v3 still send `old_id` (seen in today's logs). I can add a removal date note in the unit record."

LIVING: update when a review exchange goes wrong in a new way.
