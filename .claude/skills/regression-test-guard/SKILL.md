---
name: regression-test-guard
description: Use when writing or changing a test that guards a fix or a new feature, before writing the implementation, and whenever a test passed on the first run. Makes sure the test can actually catch the bug.
---
Adapted from: obra/superpowers test-driven-development + our lessons (a fixture carried a top-level field production never sends, so the fix was a silent no-op while the test stayed green; a test asserted through the function under test).

**Core rule: if you did not watch the test fail on the old code, you do not know it tests anything.**

## RED - write it first
- One behaviour, a clear name, real code (mocks only when unavoidable).
- Build the fixture from a REAL captured shape (a logged response, a real row), never a hand-written guess. If production nests the field, the fixture nests it the same way.
- Assert off the raw data or an independent signal - never by calling the function under test on its own output (circular).
- Run it: it MUST fail, for the expected reason (feature missing, not a typo or import error).

## GREEN - minimal code
Write the least code that passes. No extras "while here". Then run the WHOLE project suite, not just your file; report any failure by name, including ones you did not cause.

## PROVE THE GUARD
Swap the old code back via a file copy (not a stash that can tangle other work) -> the test fails; restore -> it passes. A test that passes both ways guards nothing.

## Also
- Ordering / filter / ranking fix: the test input must be one where the default order would NOT already look correct.
- A user-visible symptom gets an end-to-end scenario too (negative: the bad output is absent; positive: each acceptance point is present), if the project has a scenario suite.
- A CLASS of bug (e.g. fallback between two sources of truth) gets a test that fails on the pattern, not just on today's instance.

## Rationalizations - reject
| Thought | Reality |
|---|---|
| "Too simple to test" | Simple code breaks; the test takes a minute. |
| "I'll test after" | Tests written after pass immediately and prove nothing. |
| "I tested it manually" | Not repeatable, not recorded. |
| "The fixture is close enough" | Close enough is how no-ops ship. |
| "It passed first time, great" | Suspicious. Prove it can fail. |

## Example
Bug: "pinned items are not listed first". RED test used a captured payload where the pinned item was the OLDEST (so default order was wrong), asserted on the pinned flag from the raw payload. Failed on old code, passed after the fix, failed again with the old file copied back.

LIVING: add a trap each time a green test let a bug through.
