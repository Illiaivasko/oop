---
name: fix-a-bug
description: Use when fixing a bug - a ticket, an audit finding, a failing scenario, something the lead or a teammate reports (фікс / поправ / виправ / баг / не працює / fix / broken). Not for new behaviour - that is build-a-feature.
---
Adapted from obra/superpowers systematic-debugging + test-driven-development + verification-before-completion, fitted to this repo.

**Core rule: no fix before the root cause is at file:line, and no "fixed" before fresh evidence.**

## 1. Understand
Live ticket in full (pull-ticket), every AC listed; `/recall <key>`; the architecture note for the area. The ACs are the test plan.

## 2. Root cause - investigate-task
Reproduce live to the OUTCOME on a healthy env (the deep health check all green, a token that verifies, sandbox input that returns data - triage-infra-first). Trace to file:line. Check the twin flow, both products in one session, restart, guest vs authed, deterministic vs LLM - and what the FE actually lets the customer do (a re-shown form is useless if its field is locked).
Find the WORKING twin (other flow, other branch, last good commit - `git log -S`) and list every difference, however small. One hypothesis at a time ("X because Y"), the smallest probe, no stacked fixes. Truly external (vendor/infra/timing)? Say so, handle it (retry, clear message, log) and route to the owner.

## 3. Narrowest fix at the right layer
`architecture` for where; `editing-prompts` for prompt text; one shared helper for both flows; no phrase lists. Write the risk table (risk-check step 1). Shared or money path -> plan to the lead, OK, then code.

## 4. Red-green guard - test before the fix
Write the guard FIRST and watch it fail for the right reason (not an import error). A unit test from the real shape that FAILS on the old code (prove with a file copy of the old version, not stash), passes on the new (regression-test-guard). A scenario in the scenario suite when the harness can drive it.

## 5. Implement, then prove
`writing-code`. Then: lint; the test suite alone and READ the count vs the known failures; live - the reported case, each risk, a healthy control (verification-before-completion). Several phrasings for anything the LLM writes. Fill the risk table's result column (risk-check step 4); no gain -> revert. One change per fix, no "while I'm here". Fix did not work -> back to step 2 with the new facts; 3 failed fixes -> stop and question the design with the lead (`architecture`), no 4th patch.

## 6. Commit and record
Single-line `<ticket> fix: ...`, `<REPO_DIR>` files only, never push. Ticket record (what / where / why / dead ends / verified on which env / open owners), the architecture note's `## Learned`, index row + `Links:`, graph.py clean, memory if reusable, `.work/misses.md` for anything caught late, session state.

## 7. Close after deploy
close-out: live re-read, one in-app demo, AC-by-AC check, comment in the lead's format.

## Rationalizations - reject
| Thought | Reality |
|---|---|
| "The diff is obviously right" | Reproduce, then fix, then reproduce again |
| "It didn't reproduce, so it's fixed" | Check every AC, not the title symptom |
| "The run failed, must be my code" | Token, store health, sandbox data first |
| "Unit tests pass" | A customer-facing fix needs the live full response |
| "Agent says fixed" | Check the diff and rerun it yourself |
| "One more try" after 2 misses | Re-investigate; after 3, it's the design |
| "I'll add the test after" | A test you never saw fail proves nothing |

The lead's signals you skipped a step: "ти скіл підтягнув?", "а демо?", "як ти тестив фікс?" -> stop, go back to the missed step.

LIVING: add the concrete miss here when a fix slips past these gates.
