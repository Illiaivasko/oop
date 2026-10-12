---
name: deep-research
description: Use when the human wants a question researched across many outside sources and answered with evidence - "deep research", "research the market / topic / options", "find sources / studies", "what is known about X", "compare these tools with sources", "ресерч", "глибоке дослідження", "проведи дослідження", "знайди джерела", "що відомо про", "порівняй з джерелами". Gives a dated report where every claim carries its source. Not for a bug in our own work (investigate-task) or checking claims someone already made (verify-claims).
---
Adapted from https://github.com/anthropics/claude-cookbooks@9c1e493ddd2b patterns/agents/prompts/research_lead_agent.md + research_subagent.md (MIT); https://github.com/daymade/claude-code-skills@97a76952771a deep-research (MIT); https://github.com/mohitagw15856/pm-claude-skills@d3897cee0eed skills/source-triangulation + desk-research-sprint (MIT); rules borrowed from Socialpranker/deepdive and Weizhena/Deep-Research-skills (MIT, ideas only) - see NOTICE.

**Core rule: no claim without its source.** Every factual claim in the report carries a locator (URL + date seen, or a file path) from a retrieval made in THIS run, or it is marked `[unverified]`. Notes and memory are leads, never proof.

## When
- An open question that needs outside evidence: a market, a technology, a policy, "what is known about X", "which options exist".
- Not: a defect in our own system (`investigate-task`), checking a given text or stat (`verify-claims`), picking between options already known (`decide` - it can call this skill for missing facts).

## 0. Set up
- `As of: YYYY-MM-DD` = today. Every time-sensitive claim is judged against it.
- Read the workspace research folder (`<workspace>/research/`, `<workspace>` = `workspace:` in the project profile) for an earlier report on the topic. Reuse it only after reopening its decisive sources and checking they are still fresh.
- Outbound rule: web queries carry topic words only. NEVER paste the human's private material, internal names, file paths, code or anything secret-shaped into a search. NEVER web-search the human's private documents. No paid or metered search service and no hosted research API without the human's yes; the agent's own search and fetch tools are enough.

## 1. Decide the query type and size
| Type | Signal | Plan | Workers |
|---|---|---|---|
| Straightforward | one fact, one good source likely | one direct path + one cross-check | 1 |
| Depth-first | one question, many angles | 3-5 perspectives (methods, schools, stakeholders) | 2-4 |
| Breadth-first | N items x M fields ("compare 8 tools on price, licence, ...") | one worker per group of items; a fixed fields table; unsure cells `[unverified]` | 3-5, max 10 |
Fewer, more capable workers beat many narrow ones. Size by the number of open decision questions, not by prompt length.

## 2. Question map (the plan)
Turn the request into 2-5 decision questions. Per question write:
- **Decision question** - what it settles for the human.
- **Load-bearing claims** - provisional claims that would change the answer.
- **Disconfirming evidence** - what would weaken each one; at least one opposition query per load-bearing claim ("X criticism", "problems with X", "X failed").
- **Evidence route** - who can actually observe the fact (the original filing, dataset, docs, changelog), not who repeats it.
- **Good-enough bar + stop rule** - what counts as answered, contradicted, or still unknown.

**Plan gate:** for a large run (more than 2 workers, or more than ~30 minutes of searching) show the question map to the human and wait for a yes or edits. A straightforward query goes straight on.

## 3. Collect
- Spawn a subagent per task if your tool has them; otherwise run the tasks one after another yourself, acting as each specialist. At most 3 at once.
- Each task brief has: one objective, the decision question, the output format (evidence packet below), what counts as a good source here and what to avoid, scope bounds, and a budget of about 5-15 searches/fetches.
- Short queries (under ~5 words), broaden if thin. Fetch the full page for anything you will cite; a snippet is never evidence.
- Flag speculation ("could", "may", forecasts), aggregators, marketing and nameless "reports say" as weak.
- Evidence packet per task: question status (answered / contradicted / unknown) + a claim table `claim | excerpt | locator | date | source type | original opened? | confidence` + counter-evidence sought and found + unknowns.
- Stop on content, not budget: when the good-enough bar is met, stop that question.

## 4. Source registry
Merge all packets into one numbered list. These numbers are FINAL.
```
Approved:
[1] Org - Title | URL | type: official/academic/industry/journalism/community | date | family: <origin> | seen YYYY-MM-DD
Dropped:
x Title | URL | reason (original not reachable / echo of [1] / stale)
```
- **Evidence family:** many URLs that repeat one press release, study or dataset are ONE source. Identical numbers across "independent" outlets are the fingerprint of one origin.
- A dropped source never comes back. A new source enters only through this registry.
- URLs only from actual retrievals - never typed from memory, never "reconstructed".

## 5. Grade each load-bearing claim
| Grade | Meaning | How to phrase it |
|---|---|---|
| Established | 2+ independent origins agree (different methods or data) | state it, cite both |
| Single-sourced | one origin, maybe echoed widely | attribute inline: "one 2025 survey by X found..." |
| Contested | independent origins disagree | give the range and both sources; do not pick a favourite |
| Unverifiable | no findable origin | `[unverified]`, or leave it out |
Also check drift: the original wording vs the circulating one ("IT projects over $1M" became "projects").
Triangulated = 3+ sources, 2+ source types, 2+ independent origins; below that, confidence is capped at medium.

## 6. Draft, then counter-review, then trace
- Write the report yourself (the lead), never a subagent. Topic-first sections, not task order.
- Every factual sentence carries `[n]` from the registry or `[unverified]`. Numbers, dates and quotes always need `[n]`.
- **Counter-review** (mandatory, zero findings allowed): could the main conclusion be wrong? which high-impact claim rests on one evidence family? which claim lacks a source that can observe the fact? which time-sensitive claim uses a stale source? Fix or mark each; never invent issues to fill the section. For a deeper pass, run `verify-claims` on the draft or `challenge` on the conclusion.
- **Trace:** every `[n]` in the text exists in Approved; every decisive figure, date and quote was re-opened at its original; no dropped source reappears.

## 7. Deliver
- Save the report as `<workspace>/research/YYYY-MM-DD-<topic>.md` (template below).
- In chat: 3-6 lines - the answer, its confidence, the biggest open unknown, the report path.
- If the findings will be posted to other people, the outward text goes through `humanizer` (and `teammate-message` when it is a message). If they feed a choice, hand off to `decide` / `explaining-decisions`.

## Report template
```markdown
# <Question>
As of: YYYY-MM-DD | Type: straightforward / depth / breadth | Confidence: high / medium / low

## Answer
<3-5 sentences, each with [n] or [unverified]>

## Findings
### <Section>
<claims with [n]> - Confidence: <level> because <one line>

## Disagreements and unknowns
- <contested claim: range, [n] vs [m]> / "none found"
- <question still unknown + what would settle it>

## Method
Questions, queries run (topic words only), workers used, what was not searched and why.

## Sources
Approved: [1] ... | Dropped: x ... (reason)
```

## Red flags
| Thought | Reality |
|---|---|
| "Three sites say it, so it's solid" | Check the origin - often one press release with reverb |
| "I remember the URL" | Only URLs from a retrieval in this run |
| "The notes say so" | Reopen the original for anything decisive |
| "No counter-evidence came up" | Did you run the opposition query? Say which |
| "One more source" past the bar | Stop; write with what you have, label the gaps |
| "I'll paste their doc into the search to find related work" | Topic words only; private material never leaves the machine |
| "The subagent can write the report" | The lead writes it |

## Example
"Which open-source password managers are actively maintained, with licence?" - breadth-first, 3 workers by item group, fields fixed (licence, last release, audit, platforms). One "independent audit" claim traced to the vendor's own blog repeated by 4 outlets: graded single-sourced, phrased "the vendor reports an audit by X (2024) [7]". Report saved with As of, 2 contested cells shown as ranges, chat summary 4 lines.

LIVING: when a run misses a source class or leaks a query, add the check to step 0 or 3.
