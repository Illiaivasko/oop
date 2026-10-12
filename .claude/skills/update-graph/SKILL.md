---
name: update-graph
description: Use when you create or finish a ticket file, a memory, an architecture note or a skill, after any investigation or fix that taught something about the code, and when the GRAPH CHECK hook fires (онови граф / граф / зв'язки / лінки / orphan / навігація). Keeps the .work + memory + skills link graph navigable.
---
**Core rule: nothing new stays unlinked, and what an investigation learned lands in the map before the task is "done".** The graph is only worth its upkeep if every task feeds it - the architecture notes went 2 days stale while 13 fixes landed, and 4 new ticket files sat unlinked.

## What the graph is
`<HOOKS_DIR>/kb/kb.py` scans the workspace (`.work/`), the agent's memory dir and the installed skills dir. A node = one `.md` (id = file stem, or the skill dir, or frontmatter `name:`). An edge = `[[name]]`, or a skill name in backticks. `python3 $HOME/<PROJECT>/.claude/hooks/kb/graph.py` = hubs, orphans, broken links; `graph.py <node>` = one node's links both ways. `kb/recall.py <key>` reads the same scan.

## Edges every node type MUST have
| Node | Links to | Also |
|---|---|---|
| Ticket file `.work/tickets/<KEY>.md` | architecture note(s) of every module touched, the memories it produced or used, related tickets | a row in `.work/tickets/README.md`; a `Links:` line at the bottom |
| Architecture note `.work/architecture/<module>.md` | the tickets whose findings it records | new facts in `## Learned <date> (verified at <sha>)` with file:line |
| Memory | related memories / tickets via `[[name]]` | its line in MEMORY.md |
| Skill | sibling skills in backticks | row in `find-skills`, router entry if it has trigger words |

## Steps
1. After the work: which modules did I read or change? Open each note, add what it lacked or had wrong (a path, a state mutation, a moved line) with verified file:line and `[[<KEY>]]`. A line ref you did not re-check gets **unverified**.
2. Ticket file: `Links:` line; index row.
3. Run `graph.py`. Fix every NEW orphan or broken link; leave artifacts (MR texts, dailies, backups) alone. Template placeholders like `[[link]]` are not broken.
4. A renamed or deleted node: grep for its old name across `.work`, memory and skills, and repoint (e.g. `fix-or-feature` -> `fix-a-bug` / `build-a-feature`).

Example (`<TICKET>`): the ticket file ends with `Links:` and one `[[...]]` per memory it used and per module note it touched; one of those module notes got `## Learned <date> (verified at <sha>)` with the new entry point at file:line.

## Red flags
| Thought | Reality |
|---|---|
| "I'll link it at the end of the day" | Compaction comes first; link it in the same step |
| "The note is roughly right" | A stale file:line sends the next search to the wrong place; re-check or mark unverified |
| "graph.py shows 8 old orphans, not mine" | Fix yours; list the old ones for the lead, don't ignore new ones among them |

LIVING: when a new node type or folder joins the scan, add its row to the table.
