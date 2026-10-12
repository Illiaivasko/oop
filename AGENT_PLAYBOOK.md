# The Agent Collaboration Playbook

A portable, project-agnostic, tool-agnostic template for making an AI coding agent
a reliable collaborator. Copy it into any repo, rename the placeholders, and adapt.

It is not tied to any one product, vendor, or CLI. The kit this ships in (`README.md`) has the
skills, hooks and workspace template that implement it. Wherever you see `<AGENT_HOME>`,
`<WORKSPACE>`, or `<UNIT>` (a ticket / task / work item), substitute your own.
Paths in prose use `$HOME`-relative style (`~/proj/...`), never a hardcoded home dir.

The whole system rests on three mechanisms that reinforce each other:
**reliable recall** (memory you can trust), **reliable skill-loading** (the right
procedure loads when its situation applies), and **record-as-you-go** (so a context
reset never loses work). Everything below serves one of those three.

---

## 1. Philosophy — why this setup exists

An agent's context is volatile: it compacts, resets, and forgets mid-task. Left alone
it will re-derive what was already decided, re-hit dead ends, improvise a procedure a
teammate already refined, and lose the "why" behind a change. The setup fights that:

- **Reliable recall** — durable knowledge lives in files, indexed and loaded every
  session, so the agent starts informed instead of guessing.
- **Reliable skill-loading** — recurring procedures are packaged and trigger on their
  situation, so the agent follows the vetted path instead of freelancing.
- **Record-as-you-go** — what/where/why is written down at each step, so if context is
  lost the work isn't. The record is the hand-off, not a chore done at the end.
- **Deterministic glue (hooks)** — the parts that must never be forgotten are enforced
  by the harness, not by the model remembering.

The test for every rule: *"If context resets right now, or a different person picks
this up in three months, can they continue from what's written down?"* If no, write
more down.

---

## 2. Environment setup — a correct working env

### A personal workspace, separate from the repo
Keep a workspace dir for working state that is NOT the code repo and is NOT committed
to it: `~/<project>/<WORKSPACE>/` (e.g. `.work/`). It holds the live buffer, per-unit
records, notes, and drafts. Separating it from the repo means your process artifacts
never pollute commits, and the whole folder is a single portable hand-off.

Recommended layout:
```
<WORKSPACE>/
  README.md              # START-HERE, auto-loaded each session (see below)
  session_state.md       # the live "right now" buffer
  project_notes.md       # durable architecture / infra / gotchas, each with a source
  units/ (tickets/)      # ONE file per work item + a README template + index
  units/README.md        # the per-unit template + current index table
  drafts/                # outward text drafts (messages, PR descriptions)
  state-backups/         # timestamped snapshots (written by the pre-compact hook)
```

### A START-HERE file, auto-loaded every session
`<WORKSPACE>/README.md` is the one file that orients a fresh session: what the project
is, where each other file lives, how memory works, the recurring workflows, env/access
notes, and known gotchas. A **session-start hook** cats it into context automatically
(see §4) so the agent never starts blind.

### A live session-state buffer
`session_state.md` is the ephemeral "right now" buffer (keep it short, ~<200 lines):
current focus (unit + state + next action), last few commits (hash + one line), open
findings (one line each), blockers (external deps + who/when), background tasks. Update
it after every meaningful step. Keep a short **hand-off block at the very top** — that
is what a person (or the agent after compaction) reads first.

### One file per work item
Every ticket/task gets its own file under `units/`. That is the "one home" for that
unit's reasoning, dead ends, and verification — never scattered across chat. Template:
```
# <UNIT id> — <title>
Status: active / blocked / in-review / done   |   Updated: YYYY-MM-DD

## Problem          what was reported — who, where.
## Root cause       the ACTUAL cause + file:line (not the symptom). "n/a" if not a bug.
## Our action       what we did — approach, commit hashes, files touched.
## Decisions & what we tried   WHY this approach; alternatives rejected; dead ends /
                    wrong layers / contaminated repros — so they aren't repeated.
## Verified         how + on WHICH env; that it fails on the old code.
## Follow-ups       downstream wiring / product or policy Q (+ owner) / re-checks / none.
## Source           commits · issue link · related memory · who decided · logs/files.
```

### Make paths portable
Never hardcode `/Users/<name>/...` or `/home/<name>/...` in hooks, scripts, configs,
prompts, or docs. Use `$HOME`, `~`, or a project-root variable. Hardcoded home dirs are
the classic reason a setup breaks on another machine or for another teammate.
This includes permission allow-lists: a rule pinned to an old home dir silently never
matches, so every "pre-approved" command re-prompts.

### An architecture map, as linked notes
Keep one short note per module (responsibility, entry points with file:line, depends-on /
used-by as links, state it owns, verified gotchas) plus an index of the request lifecycle.
Unit records link the module they touched, so the knowledge graph ties
problems -> modules -> lessons.

### One reusable flow driver ("probe")
Don't hand-write a throwaway script every time you need to see the real output. Keep one
tool that drives the app flow to a named step, the way the real client does, and dumps the
FULL response. Cheap verification is verification that actually gets done.

---

## 3. Skills — packaged procedures that load on their situation

A **skill** is a self-contained procedure the agent loads when its situation applies —
the vetted way to do a recurring job (close a unit, edit a prompt, verify a change,
write a status update). It exists because *the misses happen when a procedure exists but
wasn't followed.* A skill turns "the agent should remember to..." into "the agent loads
the steps when the trigger fires."

### Anatomy of a skill file
One folder per skill, a `SKILL.md` with YAML frontmatter + a terse body:
```markdown
---
name: <skill-name>
description: <what it does>. Load when <the concrete situation/trigger>.
---
<One line on why this exists / what miss it prevents.>

## <Steps or Rules>
- Terse, imperative, one line each. The actual procedure.
- Cross-link siblings: "+ load <other-skill> when <sub-case>."

LIVING: update this skill when the procedure changes.
```

### How to write a good one
- **Adapt before you invent.** For general-process skills (debugging, review, delegation, planning,
  verification, skill-writing) start from an established library (e.g. obra/superpowers, the vendor's
  own skill-creator) and adapt it; write from scratch only for project-specific skills.
- **The description says WHEN, never HOW.** Trigger situations + the words people actually use; if
  the description narrates the steps, the agent follows the description and skips the body.
- **Pushy, situation-based trigger.** The `description` is the whole game — the agent
  triggers off it. Name the concrete situation and phrases ("Load when editing any
  prompt or classifier rule"), and where it matters add *"load this, do NOT improvise."*
  Under-triggering is the common failure; make the trigger explicit.
- **One concern per skill.** Split "code hub" from "verify" from "write for humans."
  A skill that tries to cover everything triggers for nothing.
- **Cross-link siblings.** Each skill points to the next in the chain
  (task-protocol → find-skills → writing-code → verification-before-completion). The agent follows links.
- **Progressive disclosure.** Keep the body short; push heavy detail/examples deeper.
  The frontmatter gets it loaded; the body gives just enough to act.
- **Keep it LIVING.** When a correction, a stale example, or a changed procedure reveals
  a gap, fix the SKILL.md — not just the one-off output. End every skill with a LIVING
  line so it stays self-maintaining. Have a dedicated "update a skill" skill.
- **Real examples only.** If the skill carries an example, it's the last real approved
  output, never invented — and it must itself demonstrate the rule (a "be terse" skill
  needs a short example).

A batch ("close these 8 tickets") is N runs of the per-item skill, never one status sweep.

### Two structural skills every setup should have
- **An entry-protocol skill** — loaded FIRST for any substantive task. It sets the
  order that prevents misses:
  `understand → recall memory → find the matching skill → record → execute → close the loop.`
  (Skip the ceremony for a trivial one-off lookup.)
- **An index skill** — the situation→skill map. Loaded at the start of a task to find
  which skill(s) to load before acting. Add a row whenever a skill is created; keep each
  trigger to one line. This is how the agent reliably *discovers* the right skill.

### Worked template (a minimal SKILL.md)
```markdown
---
name: verify-change
description: Prove a change actually runs and produces the intended result, before
  calling it done. Load after any code change, before commit. Do NOT skip on green tests.
---
Green unit tests don't prove the new path fired. Before "done":

## Steps
- Confirm the new code path is actually reached (log it / breakpoint / trace once).
- Exercise the REAL end-to-end result, not a narrow probe — inspect the full output.
- Prove the guard/test FAILS on the old code (else it guards nothing).
- Record what you verified and on which environment in the unit file.

LIVING: update when the verify procedure changes.
```

---

## 4. Hooks — the deterministic glue

Hooks are harness-run commands that fire on lifecycle events. They enforce the things
that must never depend on the model remembering. Keep each one small, fast, and
non-blocking unless it is a genuine safety gate. Generic patterns:

- **Session start → load context.** Cat the START-HERE file and the top of the live
  buffer into the new session, so it starts informed.
  ```bash
  cat "$HOME/<project>/<WORKSPACE>/README.md" 2>/dev/null
  printf '\n=== CURRENT FOCUS ===\n'
  head -45 "$HOME/<project>/<WORKSPACE>/session_state.md" 2>/dev/null
  ```
- **Pre-compact → save state.** Before context compaction, snapshot the live buffer and
  remind the agent to make the top hand-off block current (that block is what survives).
  ```bash
  cp "$HOME/<project>/<WORKSPACE>/session_state.md" \
     "$HOME/<project>/<WORKSPACE>/state-backups/state-$(date +%Y%m%d-%H%M%S).md" 2>/dev/null
  echo 'PRECOMPACT: refresh the top hand-off block; a backup was saved.'
  ```
- **Per-prompt → name the skill, not just the protocol.** A generic "find the skill" nudge is skipped
  exactly when the task feels familiar. Match the prompt's wording (in every language the human uses)
  against a small table of trigger phrases and print the SPECIFIC skills to load. Extend the table
  every time a skill is missed.
- **Per-prompt → nudge the protocol.** On each user prompt, echo a one-line reminder to
  run the entry protocol (recall memory → find skill → record as you go). Cheap, keeps
  the discipline from decaying mid-session.
- **Pre-tool → safety / pre-commit gate.** Before a risky tool call (e.g. a shell
  `commit`), print the commit gate (lint + tests + a guard test that fails on old code;
  commit format; what may be staged) and optionally run the auto-fixer on staged files.
  Match on the command so it only fires when relevant.
- **Pre-commit → block debris.** Scan the staged diff's ADDED lines for temporary debug
  output (print, breakpoint/pdb, "TEMP"/"DEBUG" markers, raw-payload logging) and BLOCK the
  commit (non-zero exit) with the offending lines. Give an explicit override token for the
  rare intentional case. This is a real safety gate, so it blocks; reminders don't.
- **Stop → record check.** When the turn ends, if code changed more recently than the
  state/record files (with a small grace window), nudge to refresh them before stopping.
  Advisory, always exit 0 — never block finishing.
  ```python
  # if newest_code_mtime > state_mtime + GRACE: print("RECORD CHECK: refresh state + unit file")
  # respect a stop_hook_active flag; always return 0
  ```
- **Stop → block a reply that skipped a mandatory read or a named skill.** Two blocking Stop hooks:
  a comment draft for a unit (unit link + fenced comment) needs a live read of that unit with its comments in the
  same turn, and a "verified/checked" claim needs a `## Verified` section in the unit record naming the env; a skill
  the router named must be loaded since the last compaction (a pre-compaction copy is truncated) or skipped with
  `skip-skill <name>: <why>`, which is logged. A Stop hook may block ONLY for a class that repeated 3+ times after an
  advisory guard failed; read only the transcript tail so it stays fast on long sessions.
- **Per-prompt → on a correction, print the feedback protocol + repeat counts.** When the lead points out a miss:
  answer why, log a tagged line in the misses board, and if the tag repeats propose a structural guard now.
- **Per-prompt → recall any unit key and remind to re-read it live.** For each key in the prompt print a few recall
  lines and "re-read it (with comments) before any status, demo or comment". A BIG TASK wording prints a reminder to
  search for an established skill before designing.
- **Pre-tool → warn on contract code without the contract doc; warn on probes against a degraded env.** Both advisory.
- **Status line.** Branch + uncommitted count + the top focus line - cheap, always visible.
- **Misses repeat board.** Every miss is tagged; a counter prints tags with 2+ hits. 2nd hit → propose a structural
  guard; 3rd hit → the guard failed, redesign it.

**Self-modification is gated.** Editing the agent's own hooks/config is a change to how
the agent is governed — treat it as needing explicit human action/approval, not
something the agent does to itself mid-task. Propose the change and let the human apply
it. (Advisory hooks can safely print; enforcing/blocking behavior is a human decision.)

---

## 5. Tools & external integrations — read-only by default

Any external integration (issue tracker, chat, source host, wiki, monitoring, email)
is **read-only by default.**

- **Never call a write/mutation tool** (post comment, change status, create/edit an
  item, send a message, push/merge) **without an explicit instruction in the current
  turn** naming the action. OAuth granting write scope is not permission.
- **Propose-and-wait** for anything hard to reverse or outward-facing: describe the
  exact action/command; the human runs or approves it. Permission doesn't carry to the
  next action or a later session — ask again each time.
- **Prefer the smallest capability.** If reading is enough, don't reach for write. If
  the human wants maximum safety, have them paste content instead of authorizing an
  integration.
- **Outward text: draft, don't send.** For a comment/message/update, produce the text
  for a human to post. Drafting is not sending — mark a thing "done" only once the human
  confirms it went out.
- **Servers/infra: never touch without per-turn written permission** naming the box and
  action; then read-only diagnostics only. Any state change (delete, restart, deploy,
  config/credential edit, install) needs a separate explicit OK for that exact action.
- **Enforce read-only technically, not just by rule.** When you connect an integration
  that exposes write tools, add harness deny rules for them (send, post, react, schedule,
  edit). A rule in a doc depends on the model remembering; a deny rule does not.

---

## 6. Memory — one home per fact

Durable, cross-session knowledge lives in a memory store distinct from the working
buffer. Two rules make it trustworthy:

- **One home per fact.** Each fact lives in exactly one place. Unit reasoning / dead
  ends / verification → the unit's file. A cross-unit lesson or durable reference →
  memory, with a link back to the unit. Don't duplicate the body across both — a fact in
  two homes drifts and one copy goes stale silently.
- **An index loaded every session.** A `MEMORY.md`-style index holds one line per fact
  (a relevance description + a link to the detail file); it's loaded each session so the
  agent knows what it knows. Detail lives in per-fact files, one topic each, so recall is
  by concrete key (id, file, error text, owner), not by re-reading everything.

Practices:
- **Save a fact** only when it's non-obvious and will matter again. Don't memorize what
  the code or git history already states.
- **Give each fact a relevance line** and cross-links (`[[other-fact]]`) so recall
  surfaces the neighbourhood, not one orphan note.
- **Memory is point-in-time. Re-verify before acting.** Anything a memory names (a
  file:line, a flag, an endpoint, a token) must be re-checked against current reality
  before you trust it. If it's stale, fix or delete it now — close the loop so the next
  recall is clean.
- **Note portability.** A machine-local memory store does not travel with the repo.
  Mirror anything durable into the (portable) workspace files with a Source line, so the
  knowledge survives without the local cache.
- **Keep the graph connected.** Every unit record links its memories and the module note
  it touched, and they link back. Periodically run a link check (hubs, orphans, broken
  links): an orphan note is knowledge nobody will find again.

---

## 7. Collaboration rules — how the agent should actually work

- **Investigate before fixing.** Find the real root cause (file:line) by tracing the
  full path before writing code. Don't guess. If two attempts fail, stop and re-trace
  the whole flow rather than trying a third patch.
- **Fix at the source, not the symptom.** Fix the layer that produces the problem
  (the rule, the schema, the data source), not a downstream patch. Avoid hardcoded lists
  of strings/phrases as a primary fix — they don't catch variation and hide the defect.
  Ask: "if the input is reworded tomorrow, does the fix still hold?"
- **Don't degrade the healthy path for a rare bug (blast radius).** Weigh how many
  currently-correct cases a change touches. A fix for an edge case must not alter the
  common case. If the only options are a fragile heuristic or a broad override that
  degrades the healthy path, stop and look for a narrow structural signal — or escalate.
- **Escalate genuinely contested calls; don't decide unilaterally.** If a decision isn't
  objectively settled by the code (contradicting rules, a product/UX call, a
  policy/compliance question), surface it with a recommendation and let the right owner
  decide. Objective bugs with one correct answer, you just fix.
- **Verify the FULL result, not a narrow probe.** Green tests aren't proof the new path
  fired or that the user-visible output is right. Drive the real end-to-end flow and
  inspect the whole output. A guard test must fail on the old code, built from the real
  shape — a fixture that doesn't match reality ships a silent no-op.
- **Investigate to the outcome, across the variants.** Before rating or fixing, map the path from
  the entry to the real outcome (data persisted, money moved, what the user finally sees) and vary it:
  the twin path, two features used in one session, the degraded/dependency-failure path, a restart
  that rebuilds state, anonymous vs signed-in, the second attempt. A repro that stops one step before the outcome is
  not a repro; rate severity only after driving it to the end.
- **Stale fallbacks are a bug class.** An `a or b` fallback between two sources of truth is only
  right while `b` still holds the same thing; when data moves, it silently turns into a cross-flow
  leak. Guard the class with a test that fails on the pattern, not by remembering.
- **Verify the fix itself, by default.** Reproduce the target case and watch it behave
  correctly now; don't infer it from the diff. Pair it with a control that must stay
  unchanged. Skip the live check only for genuinely non-behavioral changes.
- **Pick inputs that actually exercise the path.** Third-party sandboxes and test data drift. If a
  path "can't be reproduced", sweep a few inputs before concluding; record which inputs
  work, and move test suites onto them - otherwise a suite goes red from data drift and
  stops protecting anything.
- **Audit your own change by risk category.** Ask concretely what the change could wrongly
  do (a new filter: what VALID input could it reject?) and test that case live - e.g. a
  whitelist built from one field when a sibling structure carries the same ids.
- **A contract change updates the contract doc.** If you change a schema, a request/response
  format, or a field, update the API contract doc in the same change and tell the consumer.
  A behavior change the consumer should know about gets a doc note too.
- **Check the twin.** When a class of thing has parallel variants (two mirrored flows,
  two similar call sites), a bug in one usually has a twin in the other. Fix both, and
  extract shared logic into one helper rather than copy-pasting the fix.
- **Assess risk before and after.** Before a change, note what else shares the path and
  why this is the right layer. After, re-check those risks and verify the top ones live.
- **Record what/where/why as you go.** Not at the end — at each step. The record is the
  hand-off.
- **After every miss, propose a preventive rule.** When a mistake could have been caught
  by a rule, skill, hook, or test, propose it (and agree the wording with the human
  before changing shared rules) — so the same miss can't recur.
- **Respect scope and secrets.** Edit only what's in scope; never read or output secrets
  (`.env`, keys, tokens, credentials); never commit them. Keep commit messages and
  outward text in the agreed format and the human's voice.
- **Mechanical edits are where silent damage happens.** A one-site change goes through a
  precise edit that asserts the old text, never a global search-and-replace; before appending
  to a file, check it ends with a newline. Re-run lint/tests after any scripted edit.
- **Teammate messages: only what the reader acts on.** Answer their asks point by point and
  state where it is (e.g. "on staging"). Leave out internal fixes that change nothing for
  them. Short, plain, no jargon.

---

## 8. Keeping it alive

This playbook, the skills, the memory, and the hooks are **living documents.** Refine
them whenever a miss reveals a gap — that is the whole point of the record-and-review
loop. After a regression or a repeated mistake:

1. Name the concrete failure and the check that would have caught it.
2. Decide where the fix belongs — a skill (a procedure was improvised or wrong), a hook
   (something must be enforced deterministically), memory (a fact was missing/stale), or
   a shared rule (behavior needs to change everywhere).
3. Make the smallest change there; agree wording for shared rules with the human first;
   never let a self-modifying config change happen without explicit human action.
4. Keep an improvement log (proposals + what was applied) and a MISSES log (one line per miss:
   what, class, why, guard added). When a class repeats, add a structural guard (test, hook,
   router), not another rule.
5. If the lesson is general (not tied to one project), fold it into THIS playbook in the
   same step - otherwise the portable version silently falls behind the live setup.

The setup is only as good as its upkeep: a stale skill or a drifted memory is worse than
none, because it's trusted. Prune and refresh as deliberately as you add.

Kit drift: a portable copy made from live skills keeps names, paths and unit keys unless it is written
generically on purpose. After every kit sync run a leak grep over the kit with the project's term list -
it must print nothing.

Related: [[process_improvement_plan]] [[task-protocol]] [[find-skills]]
