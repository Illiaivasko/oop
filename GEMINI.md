# GEMINI.md — Antigravity Agent Guidelines for OOP Coursework Repository

> [!CRITICAL]
> **FIRST ACTION FOR ANY AGENT**:
> Before answering or proposing code, read `.work/session_state.md` (top HAND-OFF block) and `.work/README.md`.
> Do not ask the user what the project state is — it is maintained there.

---

## 1. State Persistence & History Recording (MANDATORY)
1. **Continuous Recording**:
   - Update `.work/session_state.md` after EVERY substantive task, fix, or investigation.
   - Ensure `Focus:`, `Next action:`, and `Recent commits:` accurately reflect reality before completing your turn.
2. **Unit Tracking**:
   - Keep detailed reasoning, dead ends, and acceptance status in `.work/tickets/<TASK_ID>.md`.
3. **Decision & Misses Logs**:
   - Technical decisions go into `.work/decisions.md` (append-only ADRs).
   - When an edge-case fails or the user corrects you, document it in `.work/misses.md` with a preventative guard.

---

## 2. Proactive Self-Evolution & Skill Creation
> [!IMPORTANT]
> **Do not keep reusable domain workflows trapped in ephemeral chat.**
> Whenever you stabilize a non-trivial process, implement a domain feature, or learn user requirements:
> **PROACTIVELY CREATE OR UPDATE A SKILL in `.agents/skills/<skill-name>/SKILL.md`**.

Follow standard format:
```markdown
---
name: <skill-name>
description: <Concrete situation when to load this skill>. Load when <trigger phrases>.
---
## Procedure / Rules
- Step-by-step verified instructions.
```

---

## 3. Project Tooling & Verification
```bash
# Run tests
echo 'Run lab executable'

# Run linter
echo 'No linter configured yet'
```

---

## 4. Git & Commit Rules
- Conventional Commits: `feat:`, `fix:`, `chore:`, `refactor:`, `docs:`, `test:`.
- Pre-commit gate blocks temporary debug statements (`print(`, `console.log(`, `debugger;`, `pdb`) and secret files (`.env`).
