# Centro Control — Backend

## Stack
FastAPI · SQLAlchemy · Pydantic v2 · PostgreSQL (multi-schema) · Alembic · Docker

## Critical Rules
- **Never touch `app/core/auth/user.py`** — User model has no module columns; relationships are injected dynamically via `manifest.py` → `register_user_relationships()`
- **Never edit .env files** — use `.env.example` as reference only
- **CORS is `allow_origins=["*"]`** — known issue, do not expand without fixing it properly
- **Service name in docker is `api`** — always `docker-compose exec api <cmd>`

## Branch & Commit Conventions
- Branches: `feat/<name>`, `fix/<name>`, `chore/<name>`
- Commits: conventional commits (`feat:`, `fix:`, `chore:`, `docs:`)
- Never commit directly to `main`

## Architecture Docs
@docs/architecture.md        — system overview, startup sequence, schemas
@docs/module-system.md       — autodiscovery, manifest spec, automation contract
@docs/patterns.md            — model/schema/service/router/exception conventions
@docs/database.md            — multi-schema, alembic, migration conventions
@docs/testing.md             — conftest hierarchy, fixtures, test commands

## Module Docs
@docs/modules/README.md              — module registry table
@docs/modules/gym_tracker.md
@docs/modules/expenses_tracker.md
@docs/modules/macro_tracker.md
@docs/modules/flights_tracker.md
@docs/modules/travels_tracker.md
@docs/modules/calendar_tracker.md
@docs/modules/automations_engine.md

## Quick Reference
```bash
docker-compose exec api pytest                          # full suite
docker-compose exec api pytest app/modules/<mod>/tests  # module tests
docker-compose exec api alembic upgrade head            # run migrations
docker-compose exec api alembic revision --autogenerate -m "<desc>"
```
