---
name: writing-plans
description: Use when there is an approved spec or clear requirements for a multi-step task, before touching code, or when asked to "plan", "break this down" or "write the implementation plan".
---
Adapted from: obra/superpowers writing-plans + executing-plans + our lessons (plans that skipped the risk list and the twin path; a plan's tasks shared files and were handed to parallel agents).

**Core rule:** a plan is the set of decisions the implementer cannot make alone - exact files, names, signatures, spec values, and the test that proves each task. Not the code itself.

## 1. Scope check
Several independent subsystems -> one plan each. Each plan yields working, testable software on its own.

## 2. File map first
List every file created / modified and its one responsibility. Follow existing patterns (`architecture`). Files that change together live together.

## 3. Header
Goal (one sentence) - approach (2-3 sentences) - spec link - Global constraints (exact values copied from the spec) - Risks (from `risk-check`: shared paths, twin, healthy case) - Review focus (the inputs the spec implies but no test covers, most likely first).

## 4. Tasks
A task = the smallest unit with its own test cycle that a reviewer could reject independently. Per task:
- Files (create / modify with line range / test)
- Interfaces: consumes / produces (exact signatures)
- Steps, each one action with a checkable result: write failing test -> run, see it fail -> minimal code -> run, see it pass -> commit
- Tests use the spec's exact values; fixtures from real shapes (`regression-test-guard`)

## 5. Self-review
| Check | Fix |
|---|---|
| Every spec requirement has a task | add the task |
| A step that decides nothing ("handle edge cases") | make it concrete |
| A step that is the whole function body | replace with signature + test |
| Names consistent across tasks | align |
| Twin path covered | add or justify |
| Tasks sharing files marked sequential | mark |

## 6. Handoff
Save to `<WORKSPACE>/plans/<date>-<feature>.md`; ask the human to review and pick execution: inline (you, then one final review) or delegated (`delegate-to-subagents`). Execute continuously; stop only for a blocker, an unclear instruction, or a failed verification. Finish with `verification-before-completion` and `requesting-code-review`.

## Red flags
TBD / TODO lines; a plan longer than the code; no failing-test step; parallel tasks on the same file.

## Example
Task 2: "Modify `<module>/export.py:40-60`; produces `export_rows(filter: Filter) -> list[Row]`; step 1 test `test_export_respects_filter` asserts 2 of 3 fixture rows; run -> FAIL (no such function); implement; run -> PASS; commit."

LIVING: update when a plan misled an implementer.
