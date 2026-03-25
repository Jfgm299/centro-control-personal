---
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git add:*), Bash(git commit:*), Bash(git checkout:*), Bash(git branch:*)
description: Genera un commit siguiendo Conventional Commits (mensajes siempre en ingles)
---

## Context

- Current branch: !`git branch --show-current`
- Git status: !`git status --short`
- Staged diff: !`git diff --staged`
- Recent commits (style reference): !`git log --oneline -5`

## Task

Generate and execute a single git commit for the staged changes above.

**Rules (non-negotiable):**
- Commit message MUST be in **English** — always, no exceptions
- Never use `--no-verify`
- Never commit `.env` or files with credentials
- Never commit directly to `main` or `develop` — if on those branches, infer a branch name from the staged changes and create it automatically: `git checkout -b <type>/<short-name>` (valid prefixes: `feat/`, `fix/`, `chore/`, `refactor/`), then proceed with the commit on the new branch

**Format:** `<type>(<optional-scope>): <short description in imperative mood>`

Valid types:
- `feat` — new functionality
- `fix` — bug fix
- `chore` — maintenance, deps, config
- `docs` — documentation only
- `refactor` — code change with no behavior change
- `test` — adding or updating tests

Scope examples (use the module or area being changed):
- `feat(calendar): add routine exceptions support`
- `fix(automations): correct recursion depth check`
- `chore(deps): upgrade sqlalchemy to v2`
- `docs(calendar): update automation contract section`

**Body (optional):** if the why is not obvious, add a blank line + short explanation.

Stage any unstaged files that are relevant to the changes, then commit in a single step.
