---
allowed-tools: Bash(docker-compose exec:*), Read, Edit, Write, Glob
description: Scaffold a complete new module. Asks for module name if not provided as argument.
---

## Task

Create the complete structure for a new module. If no name was provided as argument, ask for it first.

## Naming conventions

- Snake case: `my_module`
- PostgreSQL schema: same as module name (exception: `automations_engine` → `automations`)

## Structure to create

```
backend/app/modules/<module_name>/
├── __init__.py              ← exports: router, register_handlers, TAGS, TAG_GROUP
├── manifest.py              ← SCHEMA_NAME, USER_RELATIONSHIPS, get_settings() if needed
├── models.py                ← re-exports all models for alembic
├── models/
│   └── my_entity.py         ← SQLAlchemy model with correct schema
├── schemas/
│   └── my_entity.py         ← Create / Response schemas (Pydantic v2)
├── services/
│   └── my_entity_service.py ← class-based singleton
├── routers/
│   └── my_entity_router.py  ← thin APIRouter
├── exceptions/
│   └── __init__.py          ← exceptions inheriting from AppException
├── handlers/
│   └── __init__.py          ← register_exception_handlers(app)
└── tests/
    ├── __init__.py
    └── conftest.py          ← data fixtures (create via API, never direct ORM)
```

## Implementation checklist

1. **`manifest.py`** — define `SCHEMA_NAME` and `USER_RELATIONSHIPS`
2. **Model** — `__table_args__ = {'schema': SCHEMA_NAME, 'extend_existing': True}` + FK to `core.users.id`
3. **`models.py`** — re-export all models with `# noqa: F401`
4. **Schemas** — separate `Create`, `Update`, `Response`; only `Response` gets `ConfigDict(from_attributes=True)`
5. **Service** — class with singleton at bottom; always filter by `user_id`; return `dict` or Pydantic model, never raw ORM object
6. **Router** — `prefix` and `tags` on the router; explicit `response_model` and `status_code` on every endpoint
7. **Exceptions** — inherit from `AppException`; handler returns `JSONResponse({"detail": exc.message})`
8. **`__init__.py`** — export `router`, `register_handlers`, `TAGS`, `TAG_GROUP`
9. **Migration** — `docker-compose exec api alembic revision --autogenerate -m "add_<module_name>"`
10. **Docs** — create `docs/modules/<module_name>.md` and add row in `docs/modules/README.md`

## Automation contract (optional)

If the module exposes triggers/actions, also create:
- `automation_registry.py` — `register(registry)` function
- `services/automation_handlers.py` — trigger and action handlers
- `automation_dispatcher.py` (optional) — connects module events to the automation engine

Read `@docs/module-system.md` for the full contract and use `calendar_tracker` as the reference implementation.
