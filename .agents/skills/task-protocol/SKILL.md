---
name: task-protocol
description: Use at the START of any substantive task - a fix, investigation, ticket, flow change - and after context compaction. MANDATORY entry point; routes to memory, skills and the ticket record.
---
The order that prevents the misses: understand -> recall -> find skill -> record -> execute -> close the loop. Do it for any substantive task (a fix, an investigation, a ticket, a flow change). Skip the ceremony for a trivial one-off (a single lookup, a one-line answer) - just answer.

## 1. Situation
State plainly what is actually being asked, on which flow / ticket / file. Don't start until it's clear; if it's ambiguous or a contested product/compliance call, surface it, don't guess.

## 2. Recall memory FIRST
Before deriving anything, search memory for a similar past case - we may have hit it and already decided/solved it. Run `/recall <key>` (`python3 $HOME/<PROJECT>/.claude/hooks/kb/recall.py <key>`) with the concrete keys (ticket key, file, flow, error text, owner) - it searches memory, tickets, session_state, architecture notes and skills at once; don't just skim MEMORY.md. Reuse the earlier decision, notes and gotchas instead of re-working them.
- Memory is point-in-time: anything it names (file, flag, endpoint, file:line) must be re-verified against current code before you trust it.
- If a memory is stale or wrong, fix or delete it now - close the loop so the next recall is clean.

## 3. Find the skill
Use `find-skills` to match the situation to the skill(s) that carry the procedure, and load them. Follow the skill; don't improvise a procedure a skill already defines.

## 4. Record AS YOU GO (not just at the end)
Keep a record in `.work/tickets/<KEY>.md` (or a named record for non-ticket work) and update it at each meaningful step:
- WHAT we did, HOW, WHERE (file:line), WHY (the decision + the alternatives rejected).
- WHAT WE TRIED THAT FAILED and why (dead ends, contaminated repros, wrong layers) - so it's not repeated.
- WHAT WE CHECKED / VERIFIED, on which env (healthy store? full flow, not a turn-1 probe?).
- OPEN QUESTIONS + the owner (`<OWNER-product>` / `<OWNER-compliance>` / `<OWNER-frontend>` / `<OWNER-backend-api>` / `<OWNER-support>`), and assumptions still unproven.

## 5. Execute
A bug fix follows `fix-a-bug`, a new feature `build-a-feature` (their gates, in order). Otherwise do the work per the skill. Verify per verification-before-completion before saying "verified". Surface contested calls; don't unilaterally resolve them.

## 6. Close the loop
At the end, write a durable memory for anything reusable - a decision, a recurring procedure, a gotcha, a wrong turn to avoid - with `[[links]]` to related memories/tickets, so the NEXT similar task finds it at step 2. Refresh the ticket record and the index row.
Link it into the graph: the ticket file links its memories and the `.work/architecture/` note of the module touched (and they link back); run `/graph <KEY>` to confirm it is not an orphan.
Anything I or the lead caught late (a correction, a near-miss, a wrong first rating) gets one line in `.work/misses.md` with its class and the guard added; a repeated class needs a structural guard, not another rule.
If the lesson is GENERAL (a new hook/skill/rule/way of working, not project-specific), also fold it into `.work/AGENT_PLAYBOOK.md` AND the matching skill/hook in the portable kit `.work/agent-setup/` in the same step - the portable copies must never lag the live setup.

LIVING: update this protocol as our way of working changes.

## Keep the graph current (every task)
When you create or finish a ticket/note/memory/skill, or learned something about the code: `update-graph` (edges each node type needs, Learned sections, graph.py clean). The Stop hook `graph-check.py` flags new orphans, broken links and architecture notes older than the code.
