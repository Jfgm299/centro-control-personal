# Centro Control — Agent Config

## Stack
FastAPI · SQLAlchemy · Pydantic v2 · PostgreSQL (multi-schema) · Alembic · Docker

## Critical Rules
- **Never touch `app/core/auth/user.py`** — User model has no module columns; relationships injected at runtime via `manifest.py` → `register_user_relationships()`
- **Never edit `.env` files** — use `.env.example` as reference only
- **CORS is `allow_origins=["*"]`** — known issue, do not expand without fixing it properly
- **Docker service is `api`** — always `docker-compose exec api <cmd>`
- **Never commit without explicit user instruction** — stage only, wait for `/commit`
- **Never add Co-Authored-By** to commits
- **Never build after changes**

## Branch & Commit Conventions
- Branch pattern: `(feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert)/<name>`
- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`, `perf:`, `style:`, `build:`, `ci:`, `revert:`
- Never commit directly to `main` or `develop`

## Config Structure

`.agents/` is the single source of truth for all AI agent config.
`.claude/` and `.opencode/` reference it via symlinks — never create config files directly in those directories.

| Type | Location |
|------|----------|
| Commands | `.agents/commands/<name>.md` |
| Docs | `.agents/docs/<name>.md` |
| Skills | `.agents/skills/<name>/SKILL.md` |

After creating a file in `.agents/`, add symlinks from the tool directories if needed:
```bash
ln -s ../.agents/<path> .claude/<path>
ln -s ../.agents/<path> .opencode/<path>
```

---

## Documentation

Load docs **on demand only** — do NOT pre-load all files at startup. Read a doc only when the task explicitly requires it.

| Doc | Path | Load when... |
|-----|------|--------------|
| Architecture | `@docs/architecture.md` | Startup sequence, schemas, docker setup |
| Module System | `@docs/module-system.md` | manifest.py, autodiscovery, automation contract spec |
| Patterns | `@docs/patterns.md` | Writing models, services, routers, exception handlers |
| Database | `@docs/database.md` | Alembic migrations, multi-schema, naming conventions |
| Testing | `@docs/testing.md` | conftest hierarchy, fixtures, how to run tests |
| Module Registry | `@docs/modules/README.md` | Overview of all modules and their status |
| gym_tracker | `@docs/modules/gym_tracker.md` | Working on gym_tracker module |
| expenses_tracker | `@docs/modules/expenses_tracker.md` | Working on expenses_tracker module |
| macro_tracker | `@docs/modules/macro_tracker.md` | Working on macro_tracker module |
| flights_tracker | `@docs/modules/flights_tracker.md` | Working on flights_tracker module |
| travels_tracker | `@docs/modules/travels_tracker.md` | Working on travels_tracker module |
| calendar_tracker | `@docs/modules/calendar_tracker.md` | Working on calendar_tracker module |
| automations_engine | `@docs/modules/automations_engine.md` | Working on the automation engine |

---

## Commands

| Command | File | What it does |
|---------|------|--------------|
| `/commit` | `@commands/commit.md` | Stage + commit with conventional commits |
| `/pr` | `@commands/pr.md` | Create PR following project template |
| `/test` | `@commands/test.md` | Run pytest at the right scope |
| `/deploy-check` | `@commands/deploy-check.md` | Pre-deploy 7-step checklist |
| `/new-module` | `@commands/new-module.md` | Scaffold a new backend module |
| `/update-docs` | `@commands/update-docs.md` | Update .agents/docs/ after code changes |
| `/prompt` | `@commands/prompt.md` | Optimize a prompt for AI agents |

---

## Skills

When working on this project, load the relevant skill(s) BEFORE writing any code.

### How to Use
1. Check the trigger column to find skills that match your current task
2. Load the skill by reading the SKILL.md file at the listed path
3. Follow ALL patterns and rules from the loaded skill
4. Multiple skills can apply simultaneously

| Skill | Trigger | Path |
|-------|---------|------|
| _(no skills yet)_ | — | — |

---

## Quick Reference

```bash
# Tests
docker-compose exec api pytest                           # full suite
docker-compose exec api pytest app/modules/<mod>/tests   # module tests
docker-compose exec api pytest app/modules/<mod>/tests -v -s  # verbose

# Migrations
docker-compose exec api alembic upgrade head
docker-compose exec api alembic revision --autogenerate -m "<desc>"
docker-compose exec api alembic history
docker-compose exec api alembic current

# Docker
docker-compose exec api <cmd>   # always 'api', never 'backend'
```
