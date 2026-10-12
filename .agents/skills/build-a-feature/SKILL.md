---
name: build-a-feature
description: Use before building a new feature or changing how a flow behaves - a new widget, field, step, chip, prompt behaviour or endpoint (нова фіча / додай / зроби щоб / feature / implement / new step). Not for fixing a bug - that is fix-a-bug.
---
Adapted from obra/superpowers brainstorming + writing-plans + executing-plans + verification-before-completion, fitted to this repo.

**Core rule: no code before the lead says yes to the design.** A short design is still a gate.

## 1. Understand the intent
- Read the live ticket in full (pull-ticket); `/recall <key>`; the `.work/architecture/` notes for the area (investigate-task "start from the map").
- Write back in chat: the outcome, who it is for, success criteria = the ticket's ACs. Separate what the ticket says from your assumptions. One focused question at a time for what's missing.
- Copy, chips, widget fields come from the design file / the ticket / the API contract doc (`<API_CONTRACT_DOC>`) - never invented (no design frame -> ask). Owner questions go out now: `<OWNER-product>`, `<OWNER-compliance>`, `<OWNER-frontend>`, `<OWNER-backend-api>`.

## 2. Classify - say it out loud
| Path | What it is here | Artifact before code |
|---|---|---|
| Spike | "can we / is it possible" | 2-3 sentence probe plan, a nod; code stays throwaway |
| Bounded | change to a flow that already exists (a chip, a field, a copy line, one handler) | short design in chat, explicit yes |
| Architectural | new subsystem/step, a new widget type, an FE contract change, both flows' state machines | written design in `.work/tickets/<KEY>.md`, yes, then a plan (step 4) |
In doubt -> the heavier path. Hidden complexity found mid-way -> stop, say so, upgrade. Never downgrade.

## 3. Design
- 2-3 approaches with trade-offs, lead with the recommendation. YAGNI.
- Place it with `architecture` (layer ownership); prompts via `editing-prompts` (which model role writes it); gates via `deterministic-handler` / `scoping-a-gate`; both flows via `twin-paths-parity`.
- What the CONSUMER can do: read the frontend repo (`<FRONTEND_REPO>`, read-only) - a step the app can't render or a field it locks makes the feature dead on arrival. A new/changed field -> the API contract doc (`<API_CONTRACT_DOC>`) + a line for `<OWNER-frontend>`.
- Risks: write the `risk | shares this path | how I'll verify` table (risk-check step 1).

## 4. Plan (architectural path only)
In the ticket file: file map (create/modify with exact paths), tasks each with its own test, the interfaces between them, a Review Focus list = the 3-5 inputs the ACs don't cover that would bite a customer (guest, restart, both flows, empty vendor result, other language). Self-review against the ACs: every AC -> a task. The lead reviews.

## 5. Build and prove
Implement per `writing-code`, task by task, each with its guard test run and READ. A deviation from the agreed design is written into the ticket file with why, and told to the lead - never a silent change. Architectural path: a fresh reviewer agent on BASE..HEAD at the end (`delegate-to-subagents` step 4). Then risk-check steps 3-4 (verify every risk live, fill the result column, revert what gave no gain). Evidence before claims: fresh output for each "done" (tests count read, live full response via verification-before-completion). Commit, record, graph, close per `fix-a-bug` steps 6-7.

## Red flags
| Thought | Reality |
|---|---|
| "It's small, I'll just build it" | Bounded still needs the in-chat yes |
| "I'll pick the copy, `<OWNER-product>` can change it" | Invented copy ships; ask first |
| "The BE part is done" | Not done until the app can use it end to end |
| "Tests pass, so the feature works" | Tests prove the code; the demo proves the feature |
| "The plan is wrong here, I'll just do it right" | Do it right AND record the ruling |
| "I'll polish the minors while I'm in there" | Scope the lead didn't ask for; list them, the lead decides |

LIVING: add the concrete miss here when a feature slips past these gates.
