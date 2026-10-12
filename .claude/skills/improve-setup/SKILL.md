---
name: improve-setup
description: Use when the human asks the agent to improve itself or its setup - "вдоскональся", "покращ сетап", "порадь скіли / тули / підходи", "що ще можна покращити", "recommend automations", "optimize the agent setup" - or when a retro or a repeated miss calls for new tooling. Analyses the workspace and the agent's own misses, searches ready sources first, and returns ranked proposals; installs nothing.
---
Adapted from Anthropic `claude-automation-recommender` (claude-plugins-official, plugin claude-code-setup, Apache-2.0, commit f359d43b4060): its analyse -> recommend 1-2 per category -> report flow. Added: any workspace kind (not only code, not only one agent tool), the agent's own miss signals, the reuse-first search order, a supply-chain review, and the kit's change gate.
Adapted from https://github.com/anthropics/claude-plugins-official (Apache-2.0, modified) - see NOTICE.

## Two modes
- **SETUP:** the first run in a project. Triggered by the session-start notice "PROJECT SETUP NOT DONE", or by the human asking to set the agent up for this project. It builds the project's own layer.
- **IMPROVE:** later runs, when asked to improve, or when a retro / repeated miss calls for it. Steps 0-5 below.

The kit itself stays universal. Everything specific to this project or domain is built here, in the project's local overlay, never in the kit.

## SETUP mode (run once, before other work)
1. **Ask the onboarding questions** the profile does not answer yet, one message, plain list:
   - what this workspace is for: code / notes vault / knowledge collection / mixed, and the goal;
   - which agent tools the human uses here;
   - the human's language for chat and for outward texts; who reads outward texts;
   - boundaries: what the agent may do Always / must Ask first / must Never do (delete, overwrite, push, send, run external services);
   - private areas the agent must never read;
   - sources of truth: trackers, docs, designs, data; read-only by default;
   - how "done" is proven here: tests, a demo, citations, a review.

   Write the answers to the project profile.
2. **Profile the workspace:** step 1 below.
3. **Search ready-made for THIS domain:** step 3 below. Include domain sources, e.g. a notes-vault skill set, a citation-first Q&A pattern, a test recorder for the project's language.
4. **Propose the project layer**, max 7 items:
   - domain skills: adapted from a source, or written from the human's examples;
   - domain gates: what must never happen here, e.g. delete a note without asking, answer without citing, edit source documents;
   - templates for the outputs people read;
   - routes with example prompts in the human's own words.

   Use the step 5 report format, plus where each item lives in the local overlay.
5. **Build only what the human approves**, in the local overlay:
   - each item with its proof: route cases pass, the gate blocks its bad case and passes a control, doctor green;
   - nothing goes into the kit. A lesson that looks universal becomes a separate kit proposal later.
   - Log every built item: `agentkit promote log --item <path> --kind <skill|gate|route|template|rule> --tag <tag> --note "<why>"`. The tag is a universal class from `core/improve/tags.yaml`, or `project:<name>` for a domain-only one.
6. **Write `<workspace>/improve/setup-done.md`** - the harness asks the human before the write (it is their sign-off); say in one line what it records: date, answers, what was built, what was rejected and why. Schedule the first retro after ~1 week of use.

## IMPROVE mode

**Core rule: recommend from evidence (the workspace + the agent's own misses), ready-made before custom, and change nothing. Every recommendation becomes a proposal the human approves.**

## 0. Read the plan first
Before recommending, read:
- the kit's design / backlog;
- open and applied proposals;
- previous improve-setup reports.

An idea already planned is not a new recommendation. Mention it only if the signals say it should move EARLIER, and say so explicitly.

## 1. Profile the workspace (read-only)
Detect the kind and record it:
- **Code:** manifests (package.json, pyproject.toml, go.mod, Cargo.toml...), frameworks, tests, CI, containers, API docs.
- **Notes vault:** `.obsidian/`, `[[wikilinks]]`, daily notes, templates, tags.
- **Knowledge / consultant:** a collection of documents, sources, Q&A logs, glossary.
- **Mixed:** list each part.

Also record:
- the agent tools in use (instruction files, skills folders, hooks configs);
- integrations (tracker, chat, design, docs);
- what the kit already has installed: skills, packs, gates, MCP.

## 2. Read the agent's own signals
These show what actually hurts, which a generic checklist cannot. Read them before recommending anything:
- the misses log + repeat board: tags with 2+ hits are the top priority;
- skill-skip log: a skill skipped 3+ times means a wrong route or a missing skill;
- gate logs and overrides: a gate overridden often is mis-scoped; a miss class with no gate needs one;
- `agentkit baseline` (prints only, writes nothing): trend against the frozen baseline;
- the last session(s): repeated manual steps the human typed, e.g. the same command, the same correction, the same paste. Count them from the session transcripts or the tool's history; a step done 3+ times is a candidate skill or command.
- A log that does not exist yet is itself a finding: "no gate log -> overrides cannot be measured".

## 3. Search ready-made first - in this order, and record what you checked
1. **Installed:** this kit's core + packs (`core/skills`, `core/packs/*/skills`), the project's local overlay, and the tool's installed plugins (e.g. the plugin list or cache dir of the agent tool, if any).
2. **Curated:** `core/improve/SOURCES.md`.
3. **Directories / web:** skills.sh, GitHub search, the tool's official plugin marketplaces. Search "<tool> skill|hook|mcp <need>".

For every candidate, a supply-chain review before recommending:
- read the full SKILL.md / script / server code;
- licence: GitHub API; if it returns null / NOASSERTION, read the LICENSE file (per-skill LICENSE in multi-licence repos). Also stars, last push, maintainer count, archived?
- what it executes, what leaves the machine, what it can write;
- pin by commit hash.
- A hosted service or MCP whose code you cannot read: judge it by what it receives (data leaving the machine), the vendor, and the guard that limits what is sent. Mark it "hosted - code not reviewable".

Reject:
- detector-bypass or "jailbreak" tools;
- unlicensed or non-commercial licences for copying (ideas only);
- abandoned repos;
- anything needing secrets in the repo.

## 4. Recommend - max 5 in total, max 2 per category
Categories:
- **Skills:** procedures.
- **Tools / MCP:** integrations, CLIs, docs, browsers.
- **Gates / hooks:** deterministic checks.
- **Approaches:** methods, e.g. TDD, spec-driven plans, EARS acceptance criteria, variation matrices, red-team review, retros.

Skip a category with nothing evidence-backed. Rank by (miss hits x severity) / (cost + risk), each scored 1-3. An item spanning categories counts once, in its main category. Prefer:
- a narrow edit to an existing skill over a new one;
- a ready tool over a custom one;
- a gate over a sentence.

## 4b. Promote to the core - every IMPROVE run
Run `agentkit promote candidates`. It scores each logged local improvement on three checks:
- (a) it fixes a universal miss class;
- (b) it holds no project words;
- (c) the same tag + kind was built in another project (machine registry).

A CANDIDATE must be (a) universal AND (b) clean; (c) seen in another project only raises its priority. For each candidate:
- add it to the report under "Promote to core", with the checks and the evidence: miss hits and measured effect in this project;
- on the human's yes, run `agentkit promote draft --item <path>`;
- make the draft universal: remove the listed project words, and rewrite its tests without project data;
- land it through the kit gate as a numbered proposal.

After the kit release, the project upgrades, re-runs its parity check and deletes its local copy. Never edit the core from a project session without that proposal.

## 5. Report (template below), then STOP
Write the report to `<workspace>/improve/reports/<date>-improve-setup.md` (`<workspace>` = `workspace:` in the project profile, e.g. `.work`) and show it.
- Install nothing. Edit nothing outside the report.
- Each accepted item becomes a kit proposal (class A/B/C) and goes through the kit change gate: why, search, impact (`agentkit refs`), proof, rollback.

```markdown
# Setup review <date>
Workspace: <kind, stack/vault/collection, tools in use, kit version + packs>
Signals: <top miss tags with hits, most-skipped skills, overridden gates, repeated manual steps>

## Recommendations (ranked)
### 1. <name> - <category>
- Why (evidence): <signal: tag x hits / log line / repeated step>
- What it gives: <one line>
- Source: <url> - licence, stars, last push, pinned commit | or "custom - nothing ready found (searched: ...)"
- Risk: <network / supply chain / data leaving / blast radius> -> guard
- Without it: <the fallback>
- Change class: A/B/C; proof: <how we show it works, incl. a case that fails without it>

## Promote to core
| Local item | Class | Checks a/b/c | Evidence | Proposed |

## Checked and rejected
| Candidate | Why not |

## Not enough evidence yet
<ideas that need more signal; what would confirm them>
```

## Red flags
| Thought | Reality |
|---|---|
| "This popular tool would be nice" | No signal from the misses or the workspace -> "not enough evidence" |
| "I'll just install it to try" | Nothing installs without a proposal and the human's yes |
| "Nothing ready exists, I'll design it" | Show the search you did; custom is the last resort |
| "10 good ideas" | Max 5; the rest go to the "not enough evidence" list |
| "The README says MIT" | Check the licence via the API and read the code that runs |

## Sibling skills
`new-skill` (building an accepted skill), `updating-skills`, `find-skills`, `humanizer` (report text read by others).
