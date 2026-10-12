---
name: twin-paths-parity
description: Use when fixing or investigating a bug in any code path that has a mirrored sibling - two product flows built the same way, sync and async variants, two platforms, create vs update, two similar call sites. MANDATORY at the start of such a bug; a bug in one twin usually exists in the other.
---
Adapted from: our twin-flow parity skill + obra/superpowers systematic-debugging (pattern analysis: find the working example) + our lessons (a retry-safe guard existed on one twin's order path and not the other, which shipped a double order; a question solved on one twin was re-investigated from scratch on the other).

**Core rule:** a bug worded for one twin almost always has a twin the reporter did not hit. Check and fix BOTH directions before calling it done.

## 1. Precedent check FIRST
Before investigating from scratch, search the sibling's history - code, unit records, closed tickets, memory - for the same question. Reusing its resolution can save a day.

## 2. Map the twins
Keep a twin table in the project `architecture` skill (path A method <-> path B method). If none exists, grep by the naming pattern and start one.

## 3. Compare per layer
| Layer | Check |
|---|---|
| Input / schema / validation | same fields, same constraints |
| Rules / prompts / config | same rule present in both |
| Deterministic handlers | same guard, same retry / idempotency |
| Output builders | same fields, same empty / error messaging |
| State / persistence | same reset, same flush, same ownership checks |
List EVERY difference between the working and the broken twin, however small.

## 4. Fix once
Extract the shared logic into ONE helper both twins call. Do not copy-paste the fix. If the twins legitimately differ, write down WHY in the commit message and the unit record.

## 5. Verify both
Live check on BOTH twins + a guard test for the twin that was not reported.

## Red flags
- "The ticket only mentions A."
- Pasting the fix into B with one name changed.
- "B is probably fine."

## Example
Reported: path A shows a zero fee line. Precedent check found path B had the same bug last quarter, resolved by showing the fee only at the final step from the real upstream figure. Applied the same resolution through a shared helper; B's guard test added.

LIVING: add a layer row when a difference slips past this table.
