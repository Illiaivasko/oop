---
name: risk-check
description: Use when about to change code, config or a prompt - a fix, feature, refactor, guard, filter or "small tweak". MANDATORY before editing; sets how risks are listed, verified live, and when the full regression runs.
---
Adapted from: our risk-check (no established equivalent found) + superpowers verification-before-completion + our lessons (fixes for rare cases that degraded the healthy path; full regressions burned on a known-red state).

**Order is fixed: RISKS -> implement -> VERIFY each risk -> full regression. Never jump to the regression while a known bug or unverified risk is open.**

## 1. Risks first (before touching code)
Write down what ELSE this change could break:
- the shared path / helper / prompt block / builder it touches, and every consumer;
- the twin path (`twin-paths-parity`);
- adjacent branches: sync vs async, first call vs retry, deterministic vs model-driven, anonymous vs signed-in;
- the COMMON healthy case a fix for an edge case might degrade (blast radius);
- anything reaching money, persistence, security or an external contract.

## 2. Implement the narrowest change
Fix the target case without touching the healthy path. If the only options are a fragile heuristic (string matching) or a broad override of the common case: STOP, look for a narrow structural signal (state, flag, id), or escalate.

## 3. Verify each risk - do not assume
For EVERY risk from step 1: drive it live - the fixed case AND a control that must stay unchanged - and state what you saw. Unit-green is not enough for a shared path. A risk you cannot verify locally: say so explicitly.

## 4. Full regression - only when clean
Fix and verify everything first. Then ONE clean full run as the final gate. Triage its failures infra-first (`triage-infra-first`) before blaming code.

## Quick reference
| Change touches | Required |
|---|---|
| One private function, one caller | fix check + unit test |
| A shared path / both twins / the common case | every risk verified LIVE + control |
| Money / persistence / security / contract | the above + escalate if a risk cannot be made safe |

## Red flags
- "What did this change for requests that already worked?" has no answer.
- A regex or phrase list over free text as the primary fix.
- Starting the long suite "to see what breaks".

## Example
A new validation on the shared submit handler: listed risks = every other form using the handler. Live control on one untouched form showed it now rejected a valid empty optional field -> re-scoped the check to the one form's flag before commit.

LIVING: update when the risk / verify / regression order or the checklist changes.
