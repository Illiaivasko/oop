---
name: brainstorming
description: Use before any creative or behaviour-changing work - a new feature, component, flow or capability, "let's build", "how should we", "I have an idea" - before any implementation. Turns an idea into an approved design.
---
Adapted from: obra/superpowers brainstorming + our lessons (a fix shipped for a contested product call that the owner had not decided; copy and options were invented instead of taken from the design source).
Adapted from https://github.com/obra/superpowers (MIT) - see NOTICE.

**Hard gate:** no implementation - no product code, scaffolding or installs - until the human approves the design for the chosen path. Read-only exploration is fine.

## 1. Classify out loud
| Path | When | Artifact | Gate |
|---|---|---|---|
| Spike | "can we / is it possible", answer not code | 2-3 sentence probe plan | a nod |
| Bounded | small change to a flow that already exists here | short design in chat | explicit yes |
| Architectural | new subsystem, changed interfaces, restructuring | written spec -> `writing-plans` | spec approved |
In doubt, take the heavier path. Hidden complexity mid-task upgrades the path - stop and say so. Nothing downgrades.

## 2. Shared understanding
- Discover intent: outcome, who it is for, what success looks like. Missing? Ask ONE focused question at a time (multiple choice when possible).
- Write your understanding back; separate what they said from your assumptions; invite correction.
- Scope too big (several independent subsystems)? Decompose first; brainstorm the first piece.

## 3. Design
- Architectural: 2-3 approaches with trade-offs, lead with your recommendation; present the design in sections (components, data flow, errors, testing), check each.
- Units with one purpose and a clear interface; follow existing patterns; YAGNI ruthlessly.
- Anything not settled by code (product behaviour, policy, compliance, UX copy) -> name the owner (<OWNER-product>, <OWNER-compliance>) and get the decision; do not pick.
- User-facing copy and options come from the design / spec source. No source -> ask.

## 4. Spec (architectural only)
Write to `<WORKSPACE>/specs/<date>-<topic>.md`. Self-review: placeholders, contradictions, scope, ambiguity - fix inline. Ask the human to review; then `writing-plans`, nothing else.

## Red flags
"Too simple to need a design"; "I'll start while they read it"; "I know this kind of app, so it's bounded"; keeping spike code; one approval stretched to cover the next stage.

## Example
"Add a CSV export" -> bounded (the report view exists). Two questions (which columns? all rows or filtered?), a 4-sentence design naming files and the test, STOP, "yes" -> implement with `writing-code`.

LIVING: update when a design gate is skipped in a new way.
