---
name: find-skills
description: The index of all skills - which skill to load for which situation. Load at the START of any task to find and invoke the matching skill(s) before acting, and whenever unsure whether a skill covers what you are about to do.
---
Skills carry the real procedure for recurring work. Following the matching one is NOT optional - the misses happen when a skill exists but wasn't loaded (e.g. closing a ticket without the demo handshake). So:

## Rule
At the START of any task, scan the index below, match your situation, and INVOKE the matching skill(s) with the Skill tool BEFORE acting. If two match, load both. If none match, proceed - but if the work will recur, tell the lead it may deserve a new skill (don't self-add one for a one-off).

## Index (situation -> skill)
Tickets / tracker:
- Starting on or investigating a ticket -> `pull-ticket` (pull it live, full).
- Closing tickets / moving them to Testing or Done / a status or verification comment - ONE or a BATCH ("what can we close", "закрити тікети") -> `close-out` for EACH ticket (re-read live description+ACs+comments, demo handshake, then comment).

Before changing code:
- Fixing a bug (ticket, audit finding, failing scenario, report) -> `fix-a-bug`.
- Building a new feature or changing how a flow behaves -> `build-a-feature`.
- About to write/change ANY code -> `writing-code` (the code hub: checklist + routes to the phase-specific skills below).
- Deciding where code belongs / adding a module, handler, helper, widget, gate, constant or prompt rule -> `architecture` (+ the module note in `.work/architecture/`).
- A bug / audit finding / "is this real, how bad" / before any fix -> `investigate-task` FIRST (map the path to the outcome, vary it: twin, both-products session, degraded path, rebuild, guest, sync/stream; drive it to the end; rate after).
- Created/finished a ticket file, memory, architecture note or skill, or an investigation taught something about the code, or the GRAPH CHECK hook fired -> `update-graph`.
- Creating a new skill or rewriting a general-process one -> `new-skill` (search established skills - installed, obra/superpowers, anthropics/skills - and ADAPT; write from scratch only for project-specific skills). Editing an existing skill -> `updating-skills`.
- Reporting progress / asking the lead anything during multi-step or parallel work, or "що по плану / статус" -> `status-update` (three blocks, self-contained questions, milestones only).
- 2+ tickets/fixes queued, a board sweep, "in parallel", worktrees -> `ticket-pipeline` (stages, the lead's only stops, `.claude/wt.sh`).
- About to spawn subagents for a batch of investigations / fixes -> `delegate-to-subagents` (staged: read-only evidence -> my live review + the lead's OK -> worktree fixes -> independent review + live control).
- About to change any code -> `risk-check` (risks first, verify each, regression once clean).
- Editing a prompt or classifier rule -> `editing-prompts`.
- A model picks the wrong label / args / reply and the prompt may be the cause, or a prompt edit that must be proven -> `debugging-prompts` (inventory the competing rules, one hypothesis, measured before/after).
- Deciding or recommending something that changes what ships, what the lead tells the team or an earlier recommendation, or "why did you decide that / keep me in the loop" -> `explaining-decisions` (six-line explanation, discuss before acting on the lead's decisions, `<WORKSPACE>/decisions.md`).
- Adding a deterministic handler/gate/sentinel/override/re-search -> `deterministic-handler` (+ `scoping-a-gate` for a gate/validation on a shared path or a gated-empty sentinel).
- Reading any upstream response (a third-party API, an SDK, a webhook, another team's service) -> `verify-external-shape`.
- Fixing/investigating a bug in one of two twin paths (e.g. two flows built the same way) -> `twin-paths-parity` (fix the twin too).
- Touching requirements.txt / bumping an SDK -> `pin-sdk`.

Verifying (before saying "verified" / before commit):
- Before ANY "verified" claim -> `verification-before-completion` steps 1-2 (pre-flight local env check: the app and its dependencies up + a deep health check of the store and cache; then the full happy path of every twin flow, FE-driven).
- Changed a message / widget copy / chips / widget data -> `verification-before-completion` step 5 (dump + eyeball the FULL response, not scenario pass/fail).
- Need to SEE the real response at a flow step (local or `<ENV>`) -> `<PROBE_SCRIPT> <flow> <input> --to <step>` (the project's probe script: drives one flow to a named step and dumps the full response) - don't hand-write a throwaway probe. Some steps only appear for specific sandbox inputs; note which.
- Proving a change actually runs -> `verification-before-completion` step 3.
- Confirming a sort/filter/flag/param really does something -> `verification-before-completion` step 4 (a control).
- Writing a unit test / scenario that guards a fix -> `regression-test-guard` (must fail on old code, real shape).
- A scenario/regression suddenly fails (esp. multi-turn context loss) -> `triage-infra-first`.

Writing for people:
- End-of-day daily -> `daily-update`. Morning stand-up -> `standup`.
- ANY message to a PM or teammate (status, estimate, 'done' reply to their asks, a question; chat or tracker) -> `teammate-message`. Never free-write it.
- Opening an MR (dev -> main / `<ENV>`) -> `mr-description`.

Project skills (one row per skill this project adds):
- `<SITUATION>` -> `<project-skill>`.
- Working on a step of a multi-step flow / its widget order -> `<project-skill>` (the flow's step sequence).
- Touching how the client's selected widget / option id is handled -> `<project-skill>` (audit every state reader of that id).

Meta:
- Starting ANY substantive task (the entry point: situation -> recall memory -> find skill -> record -> execute) -> `task-protocol`.
- A skill needs editing (the lead corrected it, example stale, procedure changed) -> `updating-skills`.
- Unsure which skill applies, or want the full list -> this skill.

LIVING: add a row here whenever a new skill is created, and keep each trigger one line.
