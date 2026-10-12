---
name: delegate-to-subagents
description: Use when about to hand several investigations, audit findings or fixes to subagents (суб агент / субагенти / делегувати / паралельно / batch of findings), or when a subagent's report comes back. Staged pipeline with gates - never fire-and-trust.
---
Adapted from obra/superpowers (subagent-driven-development, dispatching-parallel-agents, requesting-code-review, verification-before-completion) + the workflow-authoring quality patterns, fitted to this repo (one local docker env, our own rate limiter, the lead approves, no push).

**Core rule:** a subagent's claim is a lead, not evidence. Severity, "verified", "fixed" count only after I check them myself (code lines + fresh command output).

## 0. Before dispatching
- **Conflict scan:** list items that share files/interfaces; those go to ONE agent in sequence. Parallel only for independent domains (3+).
- **Ledger:** `.work/audit/ledger.md` - every decision I make is a line `Ruling: <decision> - <why> - <cost if wrong>`. No silent discards.
- **Artifacts as files:** agents write to `.work/audit/evidence/<id>.md`; I read files, I don't paste reports into context.

## 1. Investigate (parallel, READ-ONLY)
One agent per independent group. Read code + run unit tests only; NO live app calls, NO edits, NO git writes. Per item: path to the outcome (file:line), the `investigate-task` dimensions checked, a repro SCRIPT for me to run, verdict with the exact lines, a NARROW fix + what it could break, could-not-verify. Severity is a proposal.

## 2. Verify (gate - me)
- Adversarial pass on each high/medium claim: try to REFUTE it (find the consumer that neutralises it, the guard upstream, the case it can't reach). Kill it if refuted.
- Run their repro scripts live ONE AT A TIME, driven to the outcome; set the real severity.
- Completeness critic: what dimension/claim wasn't checked? That becomes work, not an assumption.
- Output to the lead: fix / defer / needs-owner (`<OWNER-product>`, `<OWNER-compliance>`, `<OWNER-frontend>`, `<OWNER-backend-api>`). Nothing is fixed before their OK.

## 3. Implement (one agent per approved fix, sequential unless files are disjoint -> then a `.worktrees/` copy with its own live server: `ticket-pipeline`, `.claude/wt.sh`)
Brief = the fix, the evidence file, the files it may touch, the binding rules by name (`writing-code`, `risk-check`, `twin-paths-parity`, `regression-test-guard`). Record BASE sha first. The agent reports a status:
| Status | My action |
|---|---|
| DONE | go to review |
| DONE_WITH_CONCERNS | read concerns; review unless correctness-critical |
| NEEDS_CONTEXT | answer fully, resume the same agent |
| BLOCKED | assess; give context or escalate - never retry unchanged |
Implementers never spawn their own reviewers.

## 4. Review (gate)
- Reviewer agent gets: the brief, the evidence file, BASE..HEAD - never my session history. Two verdicts: spec compliance (does it fix THIS, only this) AND quality (bugs, blast radius, twin, comment rules).
- Critical/Important -> fix loop: rounds 1-3 same implementer, 4-5 a fresh stronger one; each round re-runs its tests + scoped re-review. Minors -> ledger as deferred. At round 5 open: rule it (park with reason) - never silently drop.
- Then me: suite, guard fails on old code (file copy, not stash), LIVE control of the healthy path + the fixed case if drivable. Only then onto `dev`; report one line per fix + commit + what was live.

## Stop and ask the lead only for
irreversible/destructive ops; security-sensitive actions; side effects outside the worktree (push, merge, deploy, tracker/chat writes); a plan so broken every path is a guess. Everything else: rule, ledger, continue.

## Red flags - stop
- "The agent says verified / 5/5" -> no command output of mine = not verified.
- Two agents editing the same file in parallel.
- An agent's severity reused in a message to the lead without my own check.
- Pasting a long report into context instead of reading the file.

## Instruction template
Goal (one sentence) · items with id + claim + file:line · read first: `.work/architecture/index.md` + named skills · allowed / forbidden (live calls, push, `.env`, secrets) · known context not to re-report · output file + sections · report back <=10 lines with status. Every claim needs file:line + confidence (confirmed-by-code / likely / speculative).

## Every brief includes the map
Tell each investigating/implementing agent: read `.work/architecture/index.md` + the notes for the files it touches first, and report back (or write, if its brief allows edits to .work/) what the note should gain - verified file:line + ticket link. After the agent finishes, I update the notes and run graph.py (same rule as investigate-task).

LIVING: log each delegation miss (wrong severity, false "verified", conflict) here + `.work/misses.md`.
