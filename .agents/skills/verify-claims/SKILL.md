---
name: verify-claims
description: Use when someone's claims must be checked before they are repeated, sent or relied on - a draft, a doc, a deck, a stat, a quote, a teammate's or vendor's statement, a research draft - "fact-check this", "is this true", "verify this stat / number / quote", "where does this number come from", "check the facts before I send it", "фактчек", "перевір факти / цифри / твердження", "чи це правда", "звідки ця цифра", "перевір джерела". Gives a status and source per claim. Not for proving our own work is done (verification-before-completion).
---
Adapted from https://github.com/mohitagw15856/pm-claude-skills@d3897cee0eed skills/source-triangulation + skills/fact-check-pass (MIT); https://github.com/daymade/claude-code-skills@97a76952771a fact-checker, the "report, then apply after approval" step (MIT) - see NOTICE.

**Core rule: "confirmed" only with a locator.** A claim is confirmed only when a source opened in THIS check supports it, and the report names that source (URL + date seen, or file path + line). Memory, plausibility and "everyone knows" confirm nothing.

## When
- Standalone: a text or a single claim the human wants checked before it goes out or a decision rests on it.
- Inside `deep-research`: the counter-review and trace of a draft.
- Not: "is my fix working" (`verification-before-completion`); attacking a plan's logic rather than its facts (`challenge`).

## Steps
1. **Scope.** What is checked (whole text / one section / one claim), where it will be used, and how much is at stake. Load-bearing claims get a full trace; colour gets a quick check.
2. **Inventory.** Pull out every checkable claim, including implied and causal ones. Type each: number/stat, quote, name/title, date, causal ("X caused Y"), comparative/superlative ("first", "only", "largest"), characterisation. Skip opinions and instructions - but note when an opinion is dressed as fact.
3. **High-risk flags first.** Numbers, direct quotes and their attribution, named people (especially any allegation), superlatives, anything that could be defamatory, legal, medical or financial. These never pass on "probably right".
4. **Trace each claim to its origin.** Follow the citation chain (where it was met -> what it cites -> ... -> the survey, filing, dataset, transcript, doc). Record who made it, how, when, and with what incentive. Dead end = document it.
   - Sources: the human's own files and the material they gave first; then official/primary sources on the web. Web queries carry topic words only - NEVER paste the human's private text, names or internals into a search, and never web-search their private material.
   - Fetch the full source; a search snippet is not a basis.
5. **Independence and drift.** Independent = different methods or data, not different outlets; identical figures across outlets usually mean one origin. Compare the original wording with the circulating one - the drift is often the finding. Check the origin's date against today: a 2019 figure stated as current is wrong-by-age.
6. **Status per claim:**
   - **confirmed** - supported by a named source you opened;
   - **outdated** - was true, superseded (give the current value + date);
   - **wrong** - contradicted by a better source;
   - **contested** - independent sources disagree (give the range);
   - **single-sourced** - one origin only; usable with inline attribution;
   - **needs sourcing** - plausible, no source found yet; name what would settle it;
   - **unverifiable** - no findable origin; mark `[unverified]` or cut.
   Words, not emoji or colours.
7. **Fix per claim:** correct it, hedge it to what the source supports ("one 2024 survey found..."), attribute it, or cut it. Match the precision of the source ("about 1M", not "1,000,000").
8. **Report** (template below), dated. Show it in chat; save it to `<workspace>/research/YYYY-MM-DD-check-<topic>.md` when it is long or will be reused (`<workspace>` = `workspace:` in the project profile).
9. **Apply only after a yes.** NEVER edit the human's document, or anyone's, until the human approves the specific fixes. Then apply exactly those, re-read the changed lines, and list what changed. If the text goes to other people afterwards, it goes through `humanizer`.

## Report template
```markdown
# Fact-check: <what>
As of: YYYY-MM-DD | Claims: N | confirmed A, outdated B, wrong C, contested D, single-sourced E, needs sourcing F, unverifiable G

## High-risk
| # | Claim (as written, location) | Status | Source (locator, date) | Fix |

## All claims
| # | Claim | Type | Status | Origin + independence | Fix |

## Open before it can go out
- <what is still needed, from whom>

Apply these fixes? (nothing is changed until you say yes)
```

## Red flags
| Thought | Reality |
|---|---|
| "I know this is right" | Memory is not a basis - find it or mark it |
| "A reputable outlet said it" | Outlets echo single sources daily; trace to the origin |
| "Three citations" | Count origins, not citations |
| "Studies show" for one vendor survey | Phrase at the grade you found |
| "I'll just fix the typo-level facts in the doc" | No edits without a yes, however small |
| "Contested - I'll pick the likelier one" | Give the range and both sources |

## Example
A deck line: "80% of projects fail". Trace: blog -> news article -> a 2017 vendor survey of IT projects over a size threshold, self-reported. Status single-sourced + drift (scope dropped) + outdated. Fix: "a 2017 vendor survey found most large IT projects missed a target [1]". Report shown; the deck was changed only after the human said yes.

LIVING: when a claim type slips through, add it to step 2 or 3.
