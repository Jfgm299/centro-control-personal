# Architecture

## System Overview

```
Client (frontend)
      │ HTTP
      ▼
FastAPI app (backend/app/main.py)
      │
      ├── Middleware: CORS (allow_origins=["*"] — known issue)
      ├── Auth router  (JWT, /api/v1/auth/...)
      └── Module routers (auto-registered, /api/v1/<module>/...)
              │
              ├── Router → Service → SQLAlchemy ORM
              │                          │
              │                    PostgreSQL (multi-schema)
              │
              └── Automation handlers (called by automations_engine executor)
```

## Startup Sequence (main.py)

1. `import_all_models()` — importa `models.py` de cada módulo → SQLAlchemy registra todos los modelos en `Base.metadata`
2. `register_user_relationships()` — lee `USER_RELATIONSHIPS` de cada `manifest.py` e inyecta relaciones en `User` con `setattr`
3. `register_automation_handlers(registry)` — autodiscovers `automation_registry.py` en cada módulo y llama a su `register(registry)`
4. Itera `settings.INSTALLED_MODULES`, importa cada módulo con `import_module()`
5. Agrega `TAGS` y `TAG_GROUP` de cada módulo para el OpenAPI
6. Crea la app FastAPI con todos los tags
7. Aplica `custom_openapi()` — agrega `x-tagGroups` para ReDoc
8. Añade middleware CORS
9. Registra handlers de excepción (`register_handlers`) si el módulo los exporta
10. `include_router` para cada módulo en `/api/v1/<module>`

## Startup Event (FastAPI `@app.on_event("startup")`)

Después del setup de la app, el `startup_event` arranca los schedulers de módulos. **Deben arrancarse aquí, nunca en import-time** — arrancarlos antes de que SQLAlchemy termine de mapear los modelos causa races.

```python
start_cron_scheduler()          # automations_engine — ejecuta automations tipo CRON
start_calendar_scheduler()      # calendar_tracker — detecta eventos próximos, reminders vencidos
start_expenses_scheduler()      # expenses_tracker — detecta suscripciones próximas, presupuesto superado
start_flights_scheduler()       # flights_tracker — detecta vuelos próximos a salir
```

## Module Installation Process

Un módulo se activa solo con existir en `backend/app/modules/` con un `manifest.py` válido (que tenga `SCHEMA_NAME`). No hay lista manual. `get_installed_modules()` itera el directorio y lo descubre automáticamente.

## Critical Constraint: User Model

`backend/app/core/auth/user.py` define `User` **sin columnas de módulos**. Las relaciones (`user.workouts`, `user.expenses`, etc.) se inyectan en runtime por `register_user_relationships()`. **Nunca añadir columnas de módulos al modelo User.**

## Database Schema Layout

| Schema              | Contenido                          |
|---------------------|------------------------------------|
| `core`              | `users` (el único modelo core)     |
| `gym_tracker`       | workouts, exercises, sets, ...     |
| `expenses_tracker`  | expenses, categories, ...          |
| `macro_tracker`     | meals, food_items, ...             |
| `flights_tracker`   | flights, airports, ...             |
| `travels_tracker`   | trips, photos (Cloudflare R2), ... |
| `calendar_tracker`  | events, reminders, categories, ... |
| `automations`       | automations, nodes, executions, ...|

Los schemas se crean automáticamente en `alembic/env.py` antes de correr las migraciones:
```python
connection.execute(text("CREATE SCHEMA IF NOT EXISTS core"))
for schema in get_all_schemas():
    connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
```

## Docker Setup

- `db` — PostgreSQL dev (port 5432)
- `db_test` — PostgreSQL test (port 5433)
- `api` — FastAPI app (service name para `docker-compose exec`)
