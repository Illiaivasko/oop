---
name: status-update
description: Use whenever reporting progress to the lead in chat during multi-step or parallel work - a batch, a pipeline, agents running, something landed, a decision needed, or they ask "що по плану / що лишилось / де ми / статус". Also before any question to them.
---
Written from the lead's own choice: three blocks, self-contained questions, status at milestones. The lead lost track when questions came without context ("1 лишити, 2 прибрати"), agent reports arrived in fragments, and there was no single view of done / doing / waiting.

**Core rule: every status is the same three blocks, and every question can be answered without scrolling up.**

## The block (always this shape, in the lead's language - shown here in Ukrainian - short)
```
Зроблено
- <ticket>: <what changed for the customer, one line>. У dev (<sha>). Перевірено наживо ✓

Роблю
- <ticket>: <current step, one line>

Від тебе (<N>)
1. <what happened, one sentence>. <the exact choice>?
   Раджу: <option> - <why, one clause>.
2. ...
```
- "Зроблено" = only since the last block. Nothing landed -> leave the block out.
- One line per ticket. Customer terms first, the sha in brackets. No agent names, no file:line unless the lead asks.
- "Від тебе" lists EVERY open ask, re-stated in full each time (not "see above", not "1 лишити"). Messages to send and pushes count as asks.
- Demo steps, messages to send and commands are ALWAYS pasted in full where they are asked for - never "кроки вище" / "see the previous message": the terminal collapses earlier output (the lead once could not find a ticket's demo steps).
- "Роблю" lists at most 3 items; background runs are one line ("у фоні: прогін панелі").

## When
| Moment | What |
|---|---|
| Batch starts | full block |
| Something lands in dev | full block |
| A decision is needed | full block |
| Batch ends | full block + what is waiting for deploy / demos |
| Agent report, run finished, commit in a worktree | nothing, or one line if it changes the plan |
| The lead asks "що по плану" | full block |

## Red flags
| Thought | Reality |
|---|---|
| "They saw the question earlier" | Re-state it with context every time |
| "I'll relay the agent's report" | Relay the outcome for the customer, one line |
| "Quick update after each event" | Milestones only; noise is how the lead lost track |

Example (the agreed shape, made-up content):
```
Зроблено
- <TICKET>: повторне натискання «Оплатити» більше не створює друге замовлення. У dev (<sha>). Перевірено наживо ✓

Роблю
- <TICKET>: кнопки після кроку вибору дати - пишу фікс

Від тебе (2)
1. Фільтр «до 100» ховає вже показані результати. Прибрати це і для «задорого»?
   Раджу: так - клієнт має бачити всі підхожі.
2. Пуш dev - 18 комітів готові.
```

LIVING: when the lead corrects the format, update the block and the example.
