---
name: requesting-code-review
description: Use when a task, fix or feature is complete and before it merges or is reported done, after each task of a multi-task plan, when stuck, or when auditing your own batch of recent commits. Gets an independent review with the right context.
---
Adapted from: obra/superpowers requesting-code-review + our lessons (a read-only audit of my own nine commits found three regressions - but only once it was given concrete risk categories instead of "check this").

**Core rule:** review early, review often, by a reviewer that gets crafted context - never your session history - and concrete categories to hunt.

## 1. Pin the range
`BASE=$(git merge-base <base-branch> HEAD)`; `HEAD=$(git rev-parse HEAD)`. Use the sha recorded BEFORE the work started, never `HEAD~1` for a multi-commit task.

## 2. Brief the reviewer
Give: what was built (2 lines), the requirement / plan / unit record, BASE..HEAD, the binding project rules, and CATEGORIES:
| Category | Ask |
|---|---|
| Spec | does it fix THIS and only this? each acceptance point met? |
| Blast radius | what healthy case does it now change? |
| Twin | is the mirrored path fixed too? (`twin-paths-parity`) |
| Valid-input rejection | what VALID input could a new filter / check reject? |
| External shape | are field names verified from a real response? |
| Tests | does each guard fail on the old code? built from the real shape? |
| Hygiene | debug output, dead code, comment rules, contract doc updated |
Ask for findings as Critical / Important / Minor, each with file:line and a confidence.

## 3. Act on findings
- Critical: fix now. Important: fix before proceeding. Minor: note in the ledger / unit record.
- Verify each finding before acting (`receiving-code-review`); push back with evidence if wrong.
- Re-review only the fix range, scoped to the open findings.

## Red flags
- "It's simple, skip review."
- Reviewing your own diff inline instead of an independent pass.
- Handing the reviewer your whole conversation.
- Proceeding with an open Important finding.

## Example
After a batch of five fixes: reviewer briefed with BASE..HEAD and the category table. Found: a new whitelist built from one field while a sibling structure carries the same ids (Critical, valid-input rejection) - fixed with a live control before continuing.

LIVING: add a category when a review misses a class of bug.
