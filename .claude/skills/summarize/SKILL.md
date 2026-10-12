---
name: summarize
description: Use when the human wants long material made short and usable - an article, document, email or chat thread, transcript, meeting notes, or results from several sources - "summarize", "TL;DR", "the gist", "key takeaways", "action items from the meeting", "who owns what", "is it worth reading", "підсумуй", "коротко суть", "зроби саммарі", "вижимка", "екшн айтеми", "що вирішили на зустрічі", "зведи докупи з кількох джерел". Gives a faithful short version with decisions and owned actions. Not for checking whether the claims are true (verify-claims) or new research (deep-research).
---
Adapted from https://github.com/mohitagw15856/pm-claude-skills@d3897cee0eed skills/summarize-anything + skills/meeting-action-extractor (MIT); https://github.com/anthropics/knowledge-work-plugins@02ffa99ff00c enterprise-search/skills/knowledge-synthesis (Apache-2.0) - see NOTICE.

**Core rule: faithful first.** Every point traces to the material. Nothing added, sharpened or invented: no owner, date, number or conclusion that is not in the source. The caveat that changes the meaning stays in.

## When
- One source to compress (article, doc, thread, transcript) - **single mode**.
- A meeting or a thread where people agreed things - **meeting mode** (decisions + actions).
- Several sources about one question (files, notes, messages, search results the workspace can read) - **multi-source mode**.
- Not: "is this true" (`verify-claims`); "find out about X" (`deep-research`).

## Privacy
The material is the human's. NEVER web-search it, paste it into a search, or send it to an outside service to "add context". Summarise only what you were given or what the workspace can read. If outside context would help, say so and ask.

## Steps
1. **Ask only what is missing:** what they need from it (gist / decisions / "should I read it all?"), how long (one line / a paragraph / structured), and for meetings the attendees, so names resolve.
2. **Read all of it.** No summary of a part you did not read; if it is too long to read in full, say which part you covered.
3. **Pick the mode** and fill the template below.
   - **Single:** the TL;DR is the conclusion, not a topic label ("this document discusses..." is banned). 3-7 key points. Separate the author's opinion from established fact; keep the author's hedges.
   - **Meeting:** an action has an owner who agreed and a verb; "we should..." with no taker is an **orphan**, not an action. Due date as stated, else `[TBD]` - never invented. Decisions are kept apart from discussion. One line of context per action so it stands alone.
   - **Multi-source:** merge duplicates (same content, author, time, or one cites the other) and cite every place it appeared; keep DIFFERENT conclusions apart - never merge a disagreement away. Group by theme, not by source. Confidence per point = freshness x authority x agreement (a final doc beats a mid-thread chat message; newer beats older for status). Surface conflicts with dates and let the human see both.
4. **Self-check against the source:** each point findable in the material? any owner/date/number not there? the meaning-carrying caveat kept? opinion still labelled?
5. **Deliver.** In chat by default. If it goes to other people (a recap post, an email, a tracker comment), the outward text goes through `humanizer` (and `teammate-message` for a message). Never post or send it yourself unless the human said so.

## Templates
Single:
```markdown
**TL;DR:** <one sentence - the conclusion>
**Key points:**
- <point> (<where in the source, when useful>)
**Caveats / open:** <the "but only if...", unresolved items>
**Worth reading in full?** <yes/no + why, if asked>
```
Meeting / thread:
```markdown
**<meeting or thread> - <date>**
**Decisions:** <what was decided, not discussed>
**Actions:**
| # | Action | Owner | Due | Context |
**Orphans (raised, nobody took it):** "<someone should...>" - assign or drop?
**Open questions:** <question> - who should decide
```
Multi-source:
```markdown
**Answer:** <lead with it>
- <finding> - sources: <type + title/location + date>, <...> - confidence: high/medium/low
**Conflicts:** <source A (date) says X; source B (date) says Y; newest/most authoritative is ...>
**Sources:** <list with location and date>
```

## Red flags
| Thought | Reality |
|---|---|
| "Everyone knows who'd own that" | Not in the source = orphan or `[TBD]`, never a guess |
| "This caveat makes it long" | The caveat is often the whole point - keep it |
| "I'll search the web to fill in context" | Their material never goes into a search |
| "Two sources say slightly different things - I'll average" | Show both with dates |
| "I'll skim the middle" | Say what you did not read |
| "Sounds like a good takeaway" | If the source didn't say it, it doesn't go in |

## Example
A 40-message thread about a vendor change. Meeting mode: 2 decisions (switch vendor, keep the old contract until month end), 3 actions (2 with owners and dates, 1 owner with `[TBD]` date), 1 orphan ("someone should tell support") flagged with "assign or drop?". The human then asked for a team recap: drafted, run through `humanizer`, handed over for them to post.

LIVING: when a summary drops something the human needed, add the check to step 4.
