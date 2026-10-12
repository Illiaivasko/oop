---
name: scoping-a-gate
description: Use when adding a check, gate, guard, validation or sentinel on a shared path (a handler, a submit / order / payment step, a search many flows hit), or a deliberate "return empty to force a follow-up". Keeps it scoped to exactly the cases that need it.
---
Adapted from: our adding-a-gate skill (no established equivalent found) + our lessons (a signing gate keyed on ACCOUNT state instead of the selected option blocked a healthy cash purchase; an empty-by-design result was narrated to the user as "nothing found").

**Core rule:** a new gate fires ONLY for the cases that need it, keyed on the structural signal it is really about - never on a broad global state, never on text matching.

## 1. Scope
- Name the exact signal (the selected option's type, a pending flag, an id, a sentinel value).
- List the currently-working cases the gate will ALSO catch. Each one must be intended; one healthy case changed = mis-scoped.
- Prefer the narrowest owner of the signal over account / global / session-wide state.

## 2. Gated-empty is not "no results"
If the gate returns empty ON PURPOSE to force a follow-up:
- List EVERY place that narrates an empty result for that path (final message, fallbacks, redirects, error copy). Each must distinguish "empty because input is needed" from "empty because nothing matched", keyed on the sentinel / flag - never on keywords in the message.
- The re-ask must be terminal: nothing downstream (auto-fallback, redirect, default message) may overwrite it.
- Check the twin path (`twin-paths-parity`).

## 3. Verify
Live: the gated case fires; a control healthy case passes untouched (`verification-before-completion`); a guard test for both (`regression-test-guard`).

## Quick reference
| Keyed on | Verdict |
|---|---|
| The selected item / option / request field | right |
| A pending flag / sentinel set by this flow | right |
| Account-wide or global state | usually too broad |
| Words in free text | wrong layer |

## Red flags
"It only adds a check"; no list of other cases it catches; a gate on a shared handler without a control probe; an empty-by-design path with no narration audit.

## Example
A consent check was hung on every order where "the account has unsigned documents". Re-scoped to "the selected plan needs consent" - the cash path passed again, the financed path still asked.

LIVING: add a scoping trap each time a gate catches a healthy case.
