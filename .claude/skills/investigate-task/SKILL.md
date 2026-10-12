---
name: investigate-task
description: Use when a bug, audit finding, odd behaviour or "is this real / how bad" question lands, and before any fix (розберись / досліди / глянь чи відтворюється / чому так / наскільки погано / how bad). Also when a fix didn't work.
---
Adapted from obra/superpowers systematic-debugging + verification-before-completion, extended with the variant dimensions that bit this project.
Adapted from https://github.com/obra/superpowers (MIT) - see NOTICE.

**Iron law: no fix, no severity, no "verified" before the path is driven to the real outcome and the root cause is at file:line.**

## 1. Root cause
- Read the error/log/report fully (every line, the stack, the status code).
- View every screenshot attached to the ticket (`<SCREENSHOT_FETCH_SCRIPT> <TICKET>` - downloads the ticket's attached screenshots) BEFORE building a hypothesis from code: the exact input the user/client sent and the output it got name the path. A real case: a code-read chain without the screenshots pointed at the wrong path; the reply text in the screenshot named the real one in a minute.
- Reproduce reliably, with exact steps. Can't reproduce -> gather more data, don't guess.
- Recent changes: `git log -S '<pattern>'`, recent commits in the area - a stale fallback is often an old fix whose premise moved.
- Multi-component: log what enters/leaves each boundary (e.g. client -> API -> each internal layer -> upstream adapter) and find where it breaks.
- Trace backward from the bad value to where it originates; fix there.

## 2. Map the path to the OUTCOME and vary it
The end is the outcome the user sees (the transaction completed, the record created, the final output the user gets, what is persisted) - not an intermediate step or UI element. Check each dimension:
- twin path (two paths built the same way) - `twin-paths-parity`; find the WORKING twin and list every difference
- BOTH twins used in one session (state leaking between them)
- degraded path: upstream empty / timeout / 409 / 5xx - where does the turn go when the step returns nothing?
- restart / cache miss: state rebuilt from the durable store instead of the cache
- anonymous vs signed-in; each account tier (e.g. basic vs full account)
- sync vs stream; main vs follow-up tool loop; deterministic vs LLM
- retry / repeated click / second attempt
- any `a or b` fallback between two sources of truth - is `b` still the same thing?
- what the CLIENT renders and in which ORDER: read `<CONSUMER_REPO>`'s renderer before claiming "on screen" - it may re-sort or split items; an ordinal reference ("the second option") must bind to the on-screen order

## 3. Hypothesis, then test
One hypothesis ("X causes it because Y"), the smallest change or probe to test it, check, repeat. Never stack a second fix on an unproven first. After 3 failed fixes: stop and question the design (`architecture`), not a 4th patch.

## 4. Rate, then hand to the fix
Severity only now: user-visible? money or data at risk? which flow / how many users? live vs latent. State what was driven live vs read from code. Then `risk-check`; the guard test fails on old code (`regression-test-guard`).

## Rationalizations - reject
| Thought | Reality |
|---|---|
| "The options showed, so it works" | Not the outcome - pick one, reach the final step, check the saved record |
| "Subagent/report says high/medium" | A lead; find the consumer and check |
| "It's obvious, skip the repro" | Obvious bugs have wrong obvious fixes |
| "Can't force the upstream error" | Then a unit guard + say so explicitly |
| "Should work now" | Run it; no evidence = not done |

## Close
Record path, dimensions, live vs code in the ticket file. A CLASS of hole -> structural guard (test that fails on the pattern, shared helper). Anything caught late -> `.work/misses.md`.

## Start from the map, leave the map better (every investigation)
- START: `kb/recall.py <key>` and read the matching `.work/architecture/<note>.md` (via its `[[links]]` / `python3 <HOOKS_DIR>/kb/graph.py <note>`) before grepping - the note usually has the file:line entry points.
- END: whatever you learned that the note lacks or gets wrong (a path, a gotcha, a state mutation, a moved line) goes into that note's `## Learned <date>` section with verified file:line and a link to the ticket. New ticket file -> index row in `.work/tickets/README.md` + a `Links:` line. Run graph.py; no new orphan or broken link (`update-graph`).
- Why (the lead's rule): the graph only helps navigation if every investigation feeds it; the architecture notes had gone 2 days stale while 13 fixes landed.

LIVING: add a dimension each time a hole slips past all of these.
