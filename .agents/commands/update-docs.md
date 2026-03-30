---
allowed-tools: Bash(git diff:*), Bash(git log:*), Read, Edit, Write, Glob
description: Analyze recent changes and update documentation in `.agents/docs/`
---

## Context

- Changed files vs develop: !`git diff develop..HEAD --name-only`
- Recent commits (for context on why things changed): !`git log develop..HEAD --oneline`

## Task

Analyze the changed files above and update the relevant docs in `.agents/docs/` to reflect the current state of the code.

## Mapping: changed file → doc to update

| If this changed... | Update... |
|---|---|
| `app/modules/<mod>/models/` | `docs/modules/<mod>.md` — Models section |
| `app/modules/<mod>/routers/` | `docs/modules/<mod>.md` — Endpoints section |
| `app/modules/<mod>/manifest.py` | `docs/modules/<mod>.md` and `docs/module-system.md` if contract changed |
| `app/modules/<mod>/automation_registry.py` | `docs/modules/<mod>.md` — Automation Contract section |
| `app/modules/<mod>/services/` | `docs/modules/<mod>.md` — relevant service section |
| `app/core/module_loader.py` | `docs/architecture.md` and `docs/module-system.md` |
| `app/main.py` | `docs/architecture.md` — Startup Sequence |
| `alembic/versions/` | `docs/database.md` if it introduces new patterns |
| New complete module | Create `docs/modules/<mod>.md` and add row in `docs/modules/README.md` |

## Process

1. Read the changed files to understand exactly what changed (not just file names)
2. Cross-reference with the mapping above to determine which docs need updates
3. Edit only the affected sections — do not rewrite sections that did not change
4. Confirm which files were updated and what changed in each
