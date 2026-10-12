---
name: find-skills
description: The index of all skills - which skill to load for which situation. Load at the START of any task to find and invoke the matching skill(s) before acting, and whenever unsure whether a skill covers what you are about to do.
---
Skills carry the real procedure for recurring work. Following the matching one is NOT optional - the misses happen when a skill exists but wasn't loaded (e.g. closing a ticket without the demo handshake). So:

## Rule
At the START of any task, scan the index below, match your situation, and LOAD the matching skill(s) BEFORE acting (your tool's skill loader, or read the skill's SKILL.md in full). If two match, load both. If none match, proceed - but if the work will recur, tell the lead it may deserve a new skill (don't self-add one for a one-off).

## Step 0 for a BIG or new kind of task (architecture, new feature or integration, estimate, research, anything no row below covers)
1. Scan the index below and the installed skills in the session list.
2. Nothing fits -> search outside BEFORE designing: obra/superpowers skills, anthropics/skills, a web search "agent skill <topic>" (and the vendor's own guide for an SDK / protocol).
3. Found one -> load or adapt it (`new-skill`); none -> write "Skill: none found (searched: ...)" in the unit record.
4. Name the skill(s) you use in the first status to the lead, so they can see the procedure the work follows.
The router prints "BIG TASK" when the wording looks like this - it is a reminder, not the trigger; judge the task, not the words.

## Packs
Core skills work in any project, code or not. Two optional packs add skills that only make sense there; a pack skill named below exists only when that pack is installed - if it is missing, follow the core skill's own steps and say which pack would add the rest.
- `code` pack (software repos): `writing-code`, `architecture-template`, `regression-test-guard`, `twin-paths-parity`, `verify-external-shape`, `scoping-a-gate`, `triage-infra-first`, `pin-sdk`, `ticket-pipeline` (+ the `wt.sh` tool).
- `llm-app` pack (products that call a language model): `editing-prompts`, `debugging-prompts`, `deterministic-handler`.

## Index (situation -> skill)
Tickets / tracker:
- Closing tickets / moving them to Testing or Done / a status or verification comment - ONE or a BATCH ("what can we close", "закрити тікети") -> `close-out` for EACH ticket (re-read live description+ACs+comments, demo handshake, then comment).

Before changing code:
- Fixing a bug (ticket, audit finding, failing scenario, report) -> `fix-a-bug`.
- Building a new feature or changing how a flow behaves -> `build-a-feature`.
- About to write/change ANY code -> `writing-code` (the code hub: checklist + routes to the phase-specific skills below).
- Deciding where code belongs / adding a module, handler, helper, UI element, gate, constant or prompt rule -> `architecture` (+ the module note in `.work/architecture/`).
- A bug / audit finding / "is this real, how bad" / before any fix -> `investigate-task` FIRST (map the path to the outcome, vary it: twin path, both twins in one session, degraded path, rebuild, anonymous user, sync/stream; drive it to the end; rate after).
- Created/finished a ticket file, memory, architecture note or skill, or an investigation taught something about the code, or the GRAPH CHECK hook fired -> `update-graph`.
- Creating a new skill or rewriting a general-process one -> `new-skill` (search established skills - installed, obra/superpowers, anthropics/skills - and ADAPT; write from scratch only for project-specific skills). Editing an existing skill -> `updating-skills`.
- Reporting progress / asking the lead anything during multi-step or parallel work, or "what's the plan / status" -> `status-update` (three blocks, self-contained questions, milestones only).
- 2+ tickets/fixes queued, a board sweep, "in parallel", worktrees -> `ticket-pipeline` (stages, the lead's only stops, `wt.sh`).
- About to spawn subagents for a batch of investigations / fixes -> `delegate-to-subagents` (staged: read-only evidence -> my live review + the lead's OK -> worktree fixes -> independent review + live control).
- About to change any code -> `risk-check` (risks first, verify each, regression once clean).
- Editing a prompt or classifier rule -> `editing-prompts`.
- A model picks the wrong label / args / reply and the prompt may be the cause, or a prompt edit that must be proven -> `debugging-prompts` (inventory the competing rules, one hypothesis, measured before/after).
- Deciding or recommending something that changes what ships, what the lead tells the team or an earlier recommendation, or "why did you decide that / keep me in the loop" -> `explaining-decisions` (six-line explanation, discuss before acting on the lead's decisions, `<WORKSPACE>/decisions.md`).
- Adding a deterministic handler/gate/sentinel/override/re-search -> `deterministic-handler` (+ `scoping-a-gate` for a gate/validation on a shared path or a gated-empty sentinel).
- Reading any upstream response (a third-party API, an SDK, a webhook, another team's service) -> `verify-external-shape`.
- Fixing/investigating a bug in one of two twin paths (paired code paths built the same way) -> `twin-paths-parity` (fix the twin too).
- Touching a dependency manifest / bumping an SDK -> `pin-sdk`.

Verifying (before saying "verified" / before commit):
- Before ANY "verified" claim -> `verification-before-completion` steps 1-2 (local env health check first: the app and its dependencies up + a deep health check of the store and cache; then the full happy path of every twin path, driven the way the real client drives it).
- Changed a message / copy / options / output fields -> `verification-before-completion` step 5 (dump + eyeball the FULL response, not scenario pass/fail).
- Need to SEE the real response at a flow step (local or `<ENV>`) -> `<PROBE_SCRIPT> <flow> <input> --to <step>` (the project's probe script: drives one flow to a named step and dumps the full response) - don't hand-write a throwaway probe. Some steps only appear for specific sandbox inputs; note which.
- Proving a change actually runs -> `verification-before-completion` step 3.
- Confirming a sort/filter/flag/param really does something -> `verification-before-completion` step 4 (a control).
- Writing a unit test / scenario that guards a fix -> `regression-test-guard` (must fail on old code, real shape).
- A scenario/regression suddenly fails (esp. multi-turn context loss) -> `triage-infra-first`.

Writing for people:
- ANY message to a PM or teammate (status, estimate, 'done' reply to their asks, a question; chat or tracker) -> `teammate-message`. Never free-write it.

Research and thinking (any workspace):
- An open question that needs outside evidence ("research X", "what is known about") -> `deep-research` (question map, source registry, counter-review, dated report in `<workspace>/research/`).
- Checking someone's claims, stats or quotes before they are repeated or sent -> `verify-claims` (confirmed only with a locator; no edits without a yes).
- Stress-testing an existing plan, decision, proposal or text -> `challenge` (steelman, 3-5 strongest challenges, synthesis).
- Long material -> short and usable: TL;DR, meeting actions, several sources merged -> `summarize` (faithful; never web-search the human's material).
- Choosing between options -> `decide` (criteria first, a lean with confidence), then `explaining-decisions`.
- Translating or fixing a translation -> `translate` (meaning and register; names, code, URLs verbatim).

Project skills (add your own; the kit does not ship these - add a router route only once the skill exists, or skill-load-check blocks on it):
- `<SITUATION>` -> `<project-skill>`.
- Starting on or investigating a ticket -> `<project-skill>` (pull the live unit in full: text, comments, status, screenshots).
- End-of-day daily / morning stand-up / opening a merge request -> `<project-skill>` (the team's exact format, one skill each).
- Working on a step of a multi-step flow / its step order -> `<project-skill>` (the flow's step sequence).
- Touching how the client's selected item / option id is handled -> `<project-skill>` (audit every state reader of that id).

Meta:
- Starting ANY substantive task (the entry point: situation -> recall memory -> find skill -> record -> execute) -> `task-protocol`.
- The lead corrects me / points out a miss -> `task-protocol` step 6 (tag it in `misses.md`, repeats -> structural guard).
- A skill needs editing (the lead corrected it, example stale, procedure changed) -> `updating-skills`.
- Unsure which skill applies, or want the full list -> this skill.

LIVING: add a row here whenever a new skill is created, and keep each trigger one line.

## Routed situations (generated from routing.yaml - do not edit here)
<!-- agentkit:begin routes -->
| Situation | Skill |
|---|---|
| Closing a ticket - re-read live, demo, validate the ACs, draft the comment | `close-out` |
| Writing to a teammate - Slack, DM, group question, reply | `teammate-message`, `humanizer` |
| Any text a person outside this chat will read - message, comment, email, post, release note, doc | `humanizer` |
| Changing an existing skill's rules, format or example | `updating-skills` |
| Explaining a decision or a fix to the lead | `explaining-decisions`, `status-update` |
| The human asks the agent to improve itself or its setup - recommend skills, tools, gates, approaches | `improve-setup` |
| Creating a new skill (search ready sources first) | `new-skill` |
| Linking notes, fixing orphans or broken links in the knowledge graph | `update-graph` |
| Several tickets at once - worktree per group, land one at a time | `ticket-pipeline` |
| Delegating work to subagents | `delegate-to-subagents` |
| Investigating a report - reproduce, root cause, rate | `investigate-task` |
| Weighing the risks of a change before or after making it | `risk-check` |
| Building new product behaviour | `build-a-feature`, `risk-check`, `writing-code` |
| Fixing a bug in product code | `fix-a-bug`, `risk-check`, `writing-code` |
| Verifying a change works - live, full flow, evidence | `verification-before-completion` |
| Researching an open question across outside sources - a dated report with a source on every claim | `deep-research` |
| Checking someone's claims, stats or quotes against sources before they are repeated or sent | `verify-claims` |
| Stress-testing an existing plan, decision, proposal or text - steelman, strongest challenges, synthesis | `challenge` |
| Making long material short and usable - TL;DR, key points, decisions and owned actions, merged sources | `summarize` |
| Choosing between options - weighted criteria, a lean with confidence, the tiebreaker unknown | `decide` |
| Translating text or improving a literal translation - meaning and register, names and code verbatim | `translate` |
<!-- agentkit:end routes -->
