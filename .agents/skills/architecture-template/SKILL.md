---
name: architecture-template
description: TEMPLATE - copy to skills/architecture/, rename to `architecture`, and fill from the real code. Once filled, use BEFORE adding a module, handler, helper, gate, constant or prompt rule, before moving logic between layers, and whenever deciding WHERE code belongs - even for a small change.
---
Adapted from: our project architecture skill (generalised) + obra/superpowers writing-plans file-structure rules + our lessons (skipping it is how god-files, duplicated response envelopes and twin-path drift happen).

HOW TO FILL: build it from the code at a named commit (`Built from <REPO> at <sha> on <date> - re-check file:line before relying on one`). Keep one note per module in `<WORKSPACE>/architecture/` and link them. Replace every `<...>`. Delete this paragraph when done.

## 1. Layers (outer -> inner) and who owns what
| Layer | Owns | Entry point (file:line) |
|---|---|---|
| <api / transport> | <requests, schemas, response shaping> | <path:line> |
| <orchestration> | <composition, identity, session load/flush> | <path:line> |
| <domain / handlers> | <business rules, pure results> | <path:line> |
| <services> | <thin wrappers over external systems> | <path:line> |
| <adapters / clients> | <transport, auth, endpoints> | <path:line> |
| <persistence / cache> | <durable store, cache, redaction> | <path:line> |

## 2. Where a new behaviour goes (decision order)
1. <Known from state alone -> deterministic layer X, returns through helper Y>
2. <Needs a re-query -> gate in Z, keyed on a structural signal, never text matching>
3. <A high-confidence non-core intent -> handler class in H>
4. <Genuinely needs model/user judgment -> rule / prompt block in P, listed in every consumer>
5. <New external call -> adapter method + interface, then service method>

## 3. State: where it lives, who may mutate it
- <Which object owns session/request state; the ONLY functions allowed to advance it>
- <What survives a restart and how; new cross-request state must be added to <flush> or be rebuildable>
- <Ownership checks for any global cache keyed by id>

## 4. Twins
<Table of mirrored paths (A <-> B). Shared logic lives once, both call it. See `twin-paths-parity`.>

## 5. Helpers, constants, config
- <Where pure shared helpers go (focused modules, not a catch-all)>
- <Where user-facing copy, limits and error-code maps live>
- <Where model ids, timeouts and secrets-free config live>

## 6. Logging
<Logger, event naming (stable snake_case + structured fields), the correlation id every line must carry.>

## 7. Before you write the code - answer these
1. Which row in section 1 owns this? Two rows -> split the change.
2. Which option in section 2 fits first?
3. What state does it read / write? Does it survive a restart?
4. What is the twin? Both halves, or why not.
5. Does it build a response? Reuse the existing builder; no new envelope literal.
6. Will one log line tell you in 3 months that this path fired, and why?

## 8. Known smells (candidates only - do NOT fix without a unit of work)
- <god-files / god-methods with sizes>
- <duplicated logic between twins or sync/async>
- <layer inversions / bypasses>

Related: `writing-code` `risk-check` `twin-paths-parity`

LIVING: when a change moves a responsibility or adds a layer, update this skill AND the module note.
