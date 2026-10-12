---
name: verify-external-shape
description: Use when writing or changing code that reads fields from anything you do not control - a third-party API response, a webhook, an SDK return value, another team's service, a file or queue message. Never guess a field name or nesting.
---
Adapted from: our verify-upstream-shape skill (no established equivalent found) + our lessons (a fix assumed a price breakdown shape from a test fixture - the real response nested it differently and already included tax, which would have inflated every total; an `a or b` chain of plausible names shipped as a guess).

**Core rule:** a field name counts only after you have seen it in a REAL response.

## Do not trust
A test fixture (the author may have guessed) - a docstring or comment (drift) - a doc page alone - pattern-matching a sibling field - `data.get("foo") or data.get("fooAmount")` (bindless guessing).

## Procedure
1. Add a temporary log where the response is parsed: sorted keys + a truncated sample.
2. Reload and drive a real request that reaches that path.
3. Read the log: exact names, types, nesting, units (cents vs units, inclusive vs exclusive).
4. Remove the temp log in the SAME edit cycle as the real fix (the pre-commit gate blocks it otherwise).
5. Write the code for the verified shape. A second variant is added only after it too is seen for real.
6. Save a captured sample (secrets stripped) as the test fixture (`regression-test-guard`).

## Cannot verify here?
No credentials, restricted env: STOP. Do not commit. Ask the human for a real sample or access. Better to ask than to ship a data or money bug.

## Quick reference
| Evidence | Enough? |
|---|---|
| Logged live response | yes |
| Recorded sample from the same endpoint + version | yes |
| Vendor doc page | only with one of the above |
| Fixture / comment / sibling field | no |

## Red flags
"It's probably called X"; an `or`-chain of names; a fixture written before any real response was seen; a temp log left in the diff.

## Example
Needed the fee from a payment provider response. Logged keys showed `fees` under `breakdown[0]`, in minor units. Code and fixture written for that; temp log removed in the same edit.

LIVING: add a trap when a guessed shape slips through.
