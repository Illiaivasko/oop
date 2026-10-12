# Hostile Room

Adapted from https://github.com/mohitagw15856/pm-claude-skills@d3897cee0eed skills/red-team-review (MIT) - see NOTICE.

## Core Principle

Pressure-test a plan the way a hostile, expert room would, before reality does. The goal is not to be negative: surface the failure modes the author is too close to see, then turn them into concrete fixes. One fatal flaw beats ten nitpicks.

## Inputs

- **The artifact** - the plan, strategy, proposal or launch.
- **The objective** - what it must achieve. If it is not stated, infer it and say so.
- **Audience and timeline** - who it must convince, by when.
- **Constraints** - budget, people, dependencies, anything already decided.

Where detail is missing, infer the most likely version and mark it *(assumed - confirm)*. Never invent facts about the plan.

## The Room

Pick the 5-6 personas most relevant to this plan. Each gives their single sharpest challenge, in their own voice, plus the one question the plan must answer. Each persona must find something the others miss.

| Persona | Lens |
|---|---|
| The sceptical finance lead | Return, cost, opportunity cost - "what do we stop doing?" |
| The user who left | Why this won't change their mind or solve their real problem |
| The senior engineer / operator | Feasibility, hidden complexity, what breaks at scale, the unglamorous work being hand-waved |
| The competitor | How a rival neutralises or out-positions this, and the response nobody planned for |
| Legal / security / compliance | The risk that turns this into an incident |
| The data realist | Which assumed number does all the work, and what happens if it is half as good |
| The sponsor | "Why now, why us, why isn't this just a small change?" |

## Ranking

The 3-5 most dangerous blind spots, ordered by **likelihood x impact**. For each: the risk, why it is easy to miss, and an early-warning signal that it is happening.

## Pre-mortem

"It is 12 months later and this failed. Write the headline." Two or three plausible failure stories, one or two sentences each.

## Output Template

```markdown
## Hostile Room: [Plan]

### What I'm reviewing
[One sentence: the plan and the outcome it bets on. Say if the objective was inferred.]

### The room
- **[Persona]:** [sharpest challenge] - must answer: [question]

### Top blind spots (likelihood x impact)
| # | Risk | Why it's easy to miss | Early-warning signal |
|---|------|-----------------------|----------------------|

### Pre-mortem
1. [Failure story]

### Make it stronger
**Before committing:** [prioritised changes, tests to run first]
**Monitor after:** [signals to watch]
**Most dangerous assumption:** [named plainly]
```

## Anti-Patterns

- Vague objections ("it might be risky") - name the failure mode and its trigger.
- Only criticising - always end with concrete, prioritised ways to strengthen the plan.
- The same critique reworded across personas.
- Softening the most dangerous risk to be polite - put it first, plainly.
- Attacking the person instead of the plan.
