---
name: explaining-decisions
description: Whenever the agent decides or recommends something that changes what ships, what the lead tells the team, how a work item is handled, or an earlier recommendation - picking between options, not shipping or deferring something, parking a review finding, correcting a claim - or the lead asks "why did you decide that", "explain the decision", "what did you choose", "keep me in the loop". Gives the short shape of a decision explanation, how to discuss it, who decides, and the decision log.
---
Adapted from Michael Nygard's Architecture Decision Records (context, decision, consequences; a reversed decision is kept and marked superseded), MADR (considered options with pros and cons, how it will be confirmed) and Amazon's one-way / two-way doors (reversibility decides who decides). Fitted to a chat with the human lead.

**Core rule: the lead never learns about a decision from its consequences. Every decision that matters to them is explained in chat when it is made, discussed before acting when it is theirs, and logged in `<WORKSPACE>/decisions.md`.**

## The explanation (the lead's language, plain, max 6 lines)
```
Decision: <what, one line>
Why: <the evidence - a number, a log line, file:line; no "seems">
Rejected: <each real alternative> - <why, one clause>
What it changes for you: <what you test, send, wait for, or "nothing">
Reversible: easy / hard - <how>
Who decides: me / you / <OWNER-...>
```
Inside a `status-update` block it goes under the asks when the lead decides, under "done" when the agent already acted.

## Understand and discuss
- Explain so the lead can retell it to the team: plain words, the mechanism in one sentence, one real example from the case (what the user did -> what they saw). No internal jargon.
- The lead's decision: 2-3 options compared in user terms (what the user sees, the risk, the cost), a recommendation, then ask for their view and WAIT. Never act on the lead's decisions before the answer.
- "Why?" or a pushback: answer the why first, then the evidence. A pushback is information - re-check the facts, then change the plan or keep it with new data; never comply silently, never argue without new facts.
- Log the agreed outcome with the lead's reasoning.

## Who decides
| Door | Examples | What the agent does |
|---|---|---|
| Two-way, local, nobody else sees it | a measurement variant, a test harness change, an experiment on a branch, which test to add | decide, act, explain in the next status |
| One-way, or the team / users see it | landing a shared-path change, not shipping what the lead approved, a prompt rule, scope cuts, outward text, anything near money | explain + recommend, wait for the answer |
| Someone else owns it | `<OWNER-product>`, `<OWNER-compliance>`, `<OWNER-frontend>`, `<OWNER-backend-api>` | draft the question for the lead to send |

## The log `<WORKSPACE>/decisions.md`
Append-only, newest on top: `## <date> <title> - <proposed / accepted / superseded by <date title>>`, then context, decision, why, rejected options, consequences, revisit when. Never delete or rewrite an old entry: mark it superseded and add the new one.

## When
- The agent picks between options, or a measurement changes an earlier recommendation.
- It decides NOT to do something the lead asked for or approved, or defers a review finding.
- It corrects an earlier claim.
Not for mechanics nobody else sees: a search command, a file name, a temp script.

## Red flags
| Thought | Reality |
|---|---|
| "They approved it, the data says otherwise, I'll just not do it" | Explain, recommend, let them answer |
| "It's in the work-item file" | The lead reads the chat; files are for later |
| "A long explanation shows rigor" | Six lines; details go to the log |
| "I'll mention it in the daily summary" | Too late - at the moment of the decision |
| "Probably / seems" | Give the number, or say "not verified" |

## Example
The lead had approved a reply-wording change. Measured before shipping: 3 runs on 5 cases - the current build already answered correctly, and the change made the first reply echo an internal data phrase 3 times out of 3.
```
Decision: not shipping the wording change you approved
Why: 3 runs x 5 cases - current build already correct; the change broke the first reply 3/3
Rejected: ship as is - a worse first reply for no gain
What it changes for you: not in the release, nothing to test
Reversible: easy - the branch is kept
Who decides: you - you said yes, I recommend no
```

LIVING: when the lead corrects the shape, update the block and the example.
