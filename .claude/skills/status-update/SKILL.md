---
name: status-update
description: Use whenever reporting progress to the lead in chat during multi-step or parallel work - a batch, a pipeline, agents running, something landed, a decision needed, or they ask "what's the plan / what's left / where are we / status" in any language (e.g. "що по плану"). Also before any question to them.
---
Written from the lead's own choice: three blocks, self-contained questions, status at milestones. The lead lost track when questions came without context ("1 keep, 2 remove"), agent reports arrived in fragments, and there was no single view of done / doing / waiting.

**Core rule: every status is the same three blocks, and every question can be answered without scrolling up.**


## Narrate as you work (the lead asked to be kept in the loop, as if the agent thinks aloud)
- Before each step, ONE line in the human's language: what I am doing now and why ("Doing now: running the tests in a copy without .git, because that is how the gate runs them").
- After it, ONE line: what came out, including a failure and what I do about it.
- Something long in the background: say what runs, roughly how long, and that I will come back with the result. Confirm it started (its PID or first output line), then wait on that PID or a done-file - never `pgrep -f` on a string that is also in my own command line: the wait matches itself and never ends.
- Someone answered (a chat reply, a tracker comment): brief the lead FIRST in 2-4 lines - who, what they said, what it changes, the next step - then act on it.
- These one-liners are not status blocks: the full three-block status stays for milestones (below). Never go silent for several tool calls.
## Before any "what's the plan / what's left / status" - check new work first
Run ONE tracker query (read-only): every unit assigned to the lead, not done, ANY status, updated since the last look; read the NEW comments on each. A unit reassigned with "needs X" is new work for us - never "not ours" because of its title or project.
Real case: a reassigned unit with four asks was dismissed twice because the query filtered testing statuses only, until the teammate asked in chat.

## The block (always this shape, short)
Write it in the user's language from the profile - the headings too. The template is shown in English.
```
Done
- <ticket>: <what changed for the user, one line>. On <BASE_BRANCH> (<sha>). Verified live ✓

Doing
- <ticket>: <current step, one line>

From you (<N>)
1. <what happened, one sentence>. <the exact choice>?
   Recommend: <option> - <why, one clause>.
2. ...
```
- "Done" = only since the last block. Nothing landed -> leave the block out.
- One line per ticket. User-visible terms first, the sha in brackets. No agent names, no file:line unless the lead asks.
- "From you" lists EVERY open ask, re-stated in full each time (not "see above", not "1 keep"). Messages to send and pushes count as asks.
- Demo steps, messages to send and commands are ALWAYS pasted in full where they are asked for - never "steps above" / "see the previous message": the terminal collapses earlier output (the lead once could not find a ticket's demo steps).
- "Doing" lists at most 3 items; background runs are one line ("in background: panel run").
- A decision inside the block uses the six-line shape from `explaining-decisions` and goes into `decisions.md`.

## When
| Moment | What |
|---|---|
| Batch starts | full block |
| Something lands on the base branch | full block |
| A decision is needed | full block |
| Batch ends | full block + what is waiting for deploy / demos |
| Agent report, run finished, commit in a worktree | nothing, or one line if it changes the plan |
| The lead asks for the plan / status | full block |

## Red flags
| Thought | Reality |
|---|---|
| "They saw the question earlier" | Re-state it with context every time |
| "I'll relay the agent's report" | Relay the outcome for the user, one line |
| "A full status block after each event" | Full blocks at milestones only (noise is how the lead lost track); between them, one-line narration |

Example (the agreed shape, made-up content):
```
Done
- <TICKET>: pressing Save twice no longer creates a duplicate record. On <BASE_BRANCH> (<sha>). Verified live ✓

Doing
- <TICKET>: options after the date step - writing the fix

From you (2)
1. The "recent only" filter hides items the user already saw. Remove that for the "archived" filter too?
   Recommend: yes - the user should see every match.
2. Push <BASE_BRANCH> - 18 commits ready.
```

LIVING: when the lead corrects the format, update the block and the example.
