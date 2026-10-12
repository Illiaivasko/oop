---
name: challenge
description: Use when an existing plan, decision, proposal, text or recommendation (the human's or the agent's own) should be stress-tested before committing - "challenge this", "play devil's advocate", "poke holes", "stress-test", "red team", "pre-mortem", "what could go wrong", "test my assumptions", "розкритикуй", "покритикуй план", "адвокат диявола", "знайди слабкі місця", "що може піти не так", "перевір мої припущення". Gives the strongest challenges and a strengthened position. Not for generating a design from an idea (brainstorming) or weighing a code change's risks (risk-check).
---
Adapted from https://github.com/Jeffallan/claude-skills@1be15d8064f8 skills/the-fool + its 6 references (MIT); personas from https://github.com/mohitagw15856/pm-claude-skills@d3897cee0eed skills/red-team-review (MIT) - see NOTICE.

**Core rule: steelman first, then only the strongest 3-5 challenges, then a synthesis.** Attack the strongest version of the position, concede what holds, never leave the human with just a pile of objections.

## When
- A plan, decision, proposal, strategy, argument or text EXISTS and the stakes justify a hard look: before committing, sending, presenting or spending.
- The agent's own recommendation before it reaches the human on a one-way decision.
- Not: shaping a vague idea into a design (`brainstorming` builds; this attacks). Not: a code change's blast radius (`risk-check`). Not: checking facts line by line (`verify-claims` - this skill's evidence mode points there for the fact work).

## Steps
1. **Identify.** Restate the position as a steelmanned thesis: its core claim, the strongest evidence for it, what is genuinely good about it. Ask the human "is this a fair restatement?" when it was not stated explicitly.
2. **Pick a mode.** Ask the human which kind of challenge they want - use a structured choice if your tool has one, otherwise a short numbered list in chat. Offer "you choose"; then recommend one from the table below and say why in one line.
3. **Challenge.** Apply the mode's method (read its reference file). Ground every point in a concrete mechanism, number or case from THIS position - no generic "what ifs". Facts the challenge rests on carry a source, or are marked `[unverified]`.
4. **Engage.** Present the 3-5 strongest challenges, ranked. Concede points that hold. Ask the human to respond before synthesising - their answers often remove or sharpen a challenge.
5. **Synthesise.** A strengthened position: what it keeps, what it takes from the challenges, what it gives up, confidence (high / medium / low / pivot). Offer a second pass in another mode only when the first found a new category of risk or the thesis survived untouched.
6. **Hand off.** A decision that changed or survived goes to `explaining-decisions` (who decides, the log). A fact found shaky goes to `verify-claims`. Anything posted to other people goes through `humanizer`.

## Modes
| Mode | Use when you hear | Method | Reference |
|---|---|---|---|
| Expose assumptions | "obviously", "everyone knows", an untested idea | Socratic questions by theme, assumption inventory, cheap experiments | `references/socratic-questioning.md` |
| Argue the other side | "we chose X over Y", about to commit | Steelman both sides, real conflicts, synthesis pattern | `references/dialectic-synthesis.md` |
| Find failure modes | "this will definitely work", a launch, a migration | Pre-mortem: "it failed - why?", ranked narratives, warning signs, mitigations | `references/pre-mortem-analysis.md` |
| Attack it | "no one would ever...", security, incentives, competitors | Adversary profiles, ranked attack vectors, perverse incentives, defences | `references/red-team-adversarial.md` |
| Test the evidence | "the data shows", "studies show" | Claims, falsification criteria, evidence grades, competing explanations | `references/evidence-audit.md` |
| Hostile room | a plan or proposal going to a review or to decision makers | 5-6 expert personas, ranked blind spots, before-commit vs monitor-after fixes | `references/hostile-personas.md` |
Auto-pick when unsure: `references/mode-selection-guide.md`. Vague context -> expose assumptions. Many concerns -> find failure modes.

## Output template
```markdown
## Challenge: <position> - mode: <mode>
**Steelmanned thesis:** <strongest form, 2-3 lines>

**Challenges (strongest first):**
1. <challenge> - why it matters: <mechanism / number / case> - what would settle it: <test>
2. ...
**Conceded:** <points of the thesis that hold>

<Your answers to 1-3? Then I'll synthesise.>

**Synthesis:** <strengthened position> | keeps: ... | adds: ... | gives up: ...
**Confidence:** high / medium / low / pivot | **Next:** <one action or test first>
```

## Red flags
| Thought | Reality |
|---|---|
| "More objections look more thorough" | Stacking minor points fakes weakness; 3-5 strongest |
| "I'll attack the version that's easy to beat" | Strawman. Steelman, confirm, then attack |
| "Their expertise is wrong because in general..." | Generic scepticism does not override domain knowledge |
| "I'll skip the synthesis, they can figure it out" | Always end with the strengthened position |
| "I'll pick the mode for them" | Ask; recommend only when they say "you choose" |
| "It's my own recommendation, it's fine" | Your own one-way recommendations need this most |

## Example
The human plans to move the team's notes to a new tool next week. Mode chosen: find failure modes. Challenges: (1) links between notes break on import - the export drops relative links, so ~all cross-references die; (2) no rollback once the old space is archived; (3) two heavy users not consulted. Conceded: search really is better. Synthesis: pilot one folder, check links, keep the old space read-only for a month. Confidence medium; first test: import one linked folder.

LIVING: when a challenge missed something that later broke, add the pattern to the mode's reference.
