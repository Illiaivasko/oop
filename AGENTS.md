# AGENTS.md — Universal Agent Instructions for OOP Coursework Repository

> [!CRITICAL]
> **FIRST ACTION FOR ANY AGENT (GPT / Antigravity / Claude)**:
> Before answering or writing code, read `.work/session_state.md` (top HAND-OFF block) and `.work/README.md`.
> Do not ask the user what the current project state is — it is maintained there.

---

## 1. Hand-off Protocol (START HERE)
1. **Always read `.work/session_state.md` (top block) and `.work/README.md` first.**
   - `.work/session_state.md`: Contains the current focus, active task, blockers, and next action.
   - `.work/README.md`: Contains architectural overview, environment setup, and gotchas.
2. **One file per unit of work**:
   - Detailed task reasoning, decisions, and acceptance status live in `.work/tickets/<TASK_ID>.md`.
   - Update the ticket file and `session_state.md` as you make progress.
3. **Record as you go**:
   - Before ending your turn, ensure `.work/session_state.md` reflects current status so the next agent (or human) knows what to do next.

---

## 2. Project Overview & Architecture
- **Name**: `oop`
- **Description**: Educational repository for Object-Oriented Programming laboratories and practical assignments.
- **Active Focus**: Lab assignments setup & code structure

---

## 3. Tooling & Verification Commands
```bash
# Run test suite
echo 'Run lab executable'

# Run linter & formatter
echo 'No linter configured yet'
```

- **Verification before claims**: Green unit tests alone are not proof. Exercise the actual flow and verify the full output before marking a task done.
- **Regression guards**: When fixing a bug, write a guard test that fails on the old code and passes on the new code.

---

## 4. Git & Commit Rules
- **Commit Format**: Conventional Commits (`feat:`, `fix:`, `chore:`, `refactor:`, `docs:`, `test:`).
- **Strict Quality Gate**:
  - Never commit temporary debug lines (`print(`, `console.log(`, `debugger;`, `import pdb`, `# TEMP`, `# DEBUG`).
  - Never commit credentials, `.env`, `.pem`, `.key`, or database files.
  - Staged code MUST pass `echo 'No linter configured yet'` and `echo 'Run lab executable'`.
  - A deterministic git pre-commit hook is installed in `.git/hooks/pre-commit` and will block dirty commits.

---

## 5. Decision & Misses Logs
- Major technical decisions go into `.work/decisions.md` (append-only ADRs).
- If a mistake occurs, document it in `.work/misses.md` with a preventative guard rule.
- Full collaboration principles live in `AGENT_PLAYBOOK.md`.

