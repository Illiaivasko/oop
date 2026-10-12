---
name: ticket-pipeline
description: Use when 2+ tickets or fixes are queued and should close fast - a board sweep, an audit batch, "take these in parallel", worktrees (кілька тасок / паралельно / через worktree / батч / закрити всі / що лишилось - давай все). Runs them as a pipeline of isolated copies with their own live server. For one ticket use fix-a-bug / build-a-feature directly.
---
Adapted from obra/superpowers subagent-driven-development + dispatching-parallel-agents + using-git-worktrees, fitted to one local container, the lead's gates and no-push.

**Core rule: parallel where files do not overlap, one after another where they do. Each item is proven live on its own server before it lands, and it lands alone.** "Build all, merge, test at the end" is banned: one red run then has six suspects.

## Stages - a pipeline, an item moves on as soon as its stage is done
0. **Ledger** `.work/batches/<date>-<name>.md`: one line per item per stage, `Ruling: <what> - <why> - <cost if wrong>`. After compaction trust the ledger + `git log`.
1. **Investigate** - parallel read-only agents (`delegate-to-subagents` stage 1): cause at file:line, narrow fix, files + prompt blocks touched.
2. **Verify + group** - me: reproduce each on :8000; same file or same prompt block = one group, done in sequence.
3. **Implement** - one agent per group, max 3 groups live: `wt.sh new`, then `fix-a-bug` / `build-a-feature` inside it: guard red on old code, `wt.sh test`, `wt.sh serve <item> 81NN`, live probe + control, `wt.sh hits` > 0, commit in our format.
4. **Review** - fresh agent gets brief + evidence + `git diff dev...wt/<item>` as a file, never my history. Fix rounds 1-3 same agent, 4-5 a fresh stronger one.
5. **Land** - ONE at a time: `wt.sh land <item>`, then lint, the test count vs known failures, live check + control on :8000. The next item rebases on dev and re-runs its guard first.
6. **Close** - one full regression (serial, sharded), records + `update-graph`, the lead pushes, `close-out` demos one by one, `wt.sh stop` + `wt.sh rm`.

## The lead's touchpoints - the only stops
1. One message after stage 2: fix list (item, cause, fix, risk) + product questions grouped per owner as ready drafts. Items needing no answer keep moving.
2. Push/deploy. 3. In-app demos. 4. Anything destructive or outside the worktrees.
Never "shall I continue?". Every report and question follows `status-update` (full block when something lands or a decision is needed).

## Tools and limits
- `$HOME/<PROJECT>/.claude/wt.sh` new / test / serve / scen / hits / stop / list / land / rm (`rm` refuses unlanded work). The copy lives inside `<REPO_DIR>/` (= `/app` in the container) so a second server can run it - that is why not the native worktree tool.
- Max 3 probing servers (they share one LLM API key); fresh session ids (the session cache is shared); restart/rebuild paths are tested on :8000 after landing.
- Runs over ~5 min: keep the machine awake (`caffeinate -i` on macOS) - a long run once stalled twice when the laptop slept.

## Red flags
| Thought | Reality |
|---|---|
| "Test them all once merged" | Each item proven on its own server, lands alone |
| "Different blocks of the same prompt file, parallel is fine" | One sentence once moved unrelated phrases. Same prompt = same group |
| Scenario passed, `hits` = 0 | You tested :8000, not the worktree |
| "serve said serving" | An old server on that port answered the health check - `wt.sh list` shows YOUR worktree on the port, then `hits` > 0 |
| "Worktree is from this morning's dev" | Rebase + re-run the guard before `land` |
| "Agent says done" | Review verdicts + my own live check, or it does not land |

Example: a classifier experiment - 10 worktrees, 9 build agents in parallel (~6 min), all variants measured at once (8200 calls), 3 verify lenses + a critic; nothing landed before the product call.

LIVING: add each batch miss here and in `.work/misses.md`.
