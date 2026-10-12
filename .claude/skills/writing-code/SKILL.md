---
name: writing-code
description: The hub for any code change - the non-negotiable code checklist plus which related skill to pull for this specific change. Load whenever about to write or change code, after task-protocol/find-skills, before touching the file.
---
The checklist + the map of connected skills. Full rules live in the project's always-on rules file (AGENTS.md or the tool's equivalent: Code style / Comments / Code quality / Scalable-reusable-readable-debuggable / Fix at the source / Blast-radius / Risk assessment) - this skill is the working checklist and the router to the sibling skills, so a change never happens in isolation.

## Checklist (every change)
- Read the current file first; don't code from memory. Prefer editing existing files; don't add scope beyond what's asked.
- Fix at the SOURCE (the layer that produces it - prompt rule, schema, intent, deterministic data), not a symptom / hardcoded phrase list.
- Blast radius: what else shares this path (the twin path, a shared prompt block, a shared output/message builder, an adjacent branch)? A fix for a rare case must not degrade the healthy common case.
- Scalable / reusable / readable / debuggable: extract a helper if copied 2+ places; short functions; clear names; one place to look when it breaks; log key decisions.
- Mechanical edits: a single-site change goes through Edit or an asserted script (assert the exact old line), never a global sed - it silently hits every match. Appending to a file: make sure it ends with a newline first. Re-run the linter/tests after any scripted edit. zsh does not word-split an unquoted variable - loop over a literal list or an array. Check `git diff --stat` after any swap-and-restore of old code.
- Comments: default none; only a genuinely non-obvious WHY, ONE line, no names/tickets/dates in code.
- Changed the schema, the request/response format, or a UI element's fields? UPDATE the API contract doc (`<API_CONTRACT_DOC>`) to match AND flag the consumer (`<OWNER-consumer>`) - our responses MUST match that spec. A behavior change worth the consumer knowing gets a doc note too.

## Connected skills - pull the ones that fit THIS change
The overall order lives in `fix-a-bug` (a bug) or `build-a-feature` (new behaviour); this skill is their implement step.
Before / while designing:
- Always -> `risk-check` (list risks, verify each, regression only once clean).
- Deciding WHERE the code goes (new module/handler/helper/gate/UI element/constant/prompt rule, or moving logic between layers) -> `architecture` (layer ownership, where new behaviour goes, who may mutate state; map in `.work/architecture/`).
- Editing a prompt or classifier rule -> `editing-prompts` (llm-app pack).
- Adding a deterministic handler/gate/sentinel/override -> `deterministic-handler` (llm-app pack; + `scoping-a-gate` for a gate/validation on a shared path or a gated-empty).
- Reading an upstream API response -> `verify-external-shape`.
- Touching how the client's selected item / option id is handled -> the project's id-audit skill (`<project-skill>`).
- Fixing a bug in one of two twin paths -> `twin-paths-parity` (fix the twin) + the flow's step-sequence skill (`<project-skill>`, step order).
- Bumping an SDK / touching a dependency manifest -> `pin-sdk`.

After (before "done"/commit):
- `verification-before-completion` step 3 (prove it actually runs) + step 4 (a control: a flag/filter really does something).
- `regression-test-guard` (the guard test fails on old code, real shape).
- `verification-before-completion` steps 1-2 (env health check first, then the full happy path of every twin path) BEFORE saying "verified".
- Changed a message / copy / options / output fields -> `verification-before-completion` step 5 (dump + eyeball the FULL response, not just pass/fail).
- If a scenario/regression then fails oddly -> `triage-infra-first`.

## Record
Per `task-protocol`: capture WHY this layer, the alternatives rejected, what failed, and what you verified (on which env) in the ticket record as you go.

LIVING: keep this router in sync with find-skills; add a sibling here when a new code-phase skill is created.
