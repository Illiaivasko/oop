---
name: verification-before-completion
description: Use when about to claim work is done, fixed, working, verified or passing - before a commit, a status update, a close-out, or moving to the next task; also after any change to what a user sees (copy, options, response fields). Evidence before claims.
---
Adapted from: obra/superpowers verification-before-completion + our verify-full-response, smoke-flow, verify-change-fires and confirm-with-control lessons (a green suite over a fixture that faked a field; a "sorted" result that was the upstream default; a feature swallowed by try/except; fragments that hid a loop the full flow showed).

**Iron law: NO COMPLETION CLAIM WITHOUT FRESH EVIDENCE FROM THIS SESSION.** Identify the command that proves it -> run it in full -> read the output -> only then claim, quoting it.

## 1. Check the environment first
Before any live probe: the app and its dependencies are up and healthy (a deep health check, not just "port open"). After a code edit, wait for the reload to finish. A probe on a degraded env proves nothing (`triage-infra-first`).

## 2. Simple full flow first
Drive the SIMPLE happy path end to end, the way the real client does (use the ids the previous response returned; do not type shortcuts the client never sends). Both twins if there are two. Only THEN the specific fix and its edges. Never report "verified" from the edge case alone.

## 3. Prove the change fires
- Trace from entry to the changed line: will the probe reach it?
- Observe it: a log line, a populated field, a row. Not seen = not verified.
- Traps: awaiting a sync call, a try/except that swallows the feature, a threshold-gated API that silently no-ops, a wrapper that mutates input, a branch the probe never enters.

## 4. Confirm with a control
Repeat with the input removed or changed; the output MUST change because of your code. Identical output with and without = your code did nothing. Pick inputs where the default would not coincidentally look right.

## 5. Look at the FULL output
Dump the whole response (message, every field, every option) and compare against the SOURCE of truth (spec, design, contract doc), not your expectation. Values correct, not just non-null. Nothing invented, nothing missing.

## Quick reference
| Claim | Needs | Not enough |
|---|---|---|
| Tests pass | full suite output, 0 failed | one file, "should pass" |
| Bug fixed | original symptom re-driven, now correct | diff looks right |
| Guard works | fails on old code, passes on new | passes once |
| Feature works | control shows the difference | one good-looking output |
| Agent finished | diff + my own run | its report |
| Requirements met | each criterion checked | tests green |

## Red flags
"should", "probably", "looks right"; satisfaction before evidence; trusting a subagent's "verified"; a turn-1 probe for a multi-step flow.

## Example
"Sort by rating works" - output was [5,5,4,4]; the control with no sort returned the identical order, so the param was a no-op. Fixed, re-run: control differs, claim made with both outputs quoted.

LIVING: add a trap to section 3 each time one burns you.
