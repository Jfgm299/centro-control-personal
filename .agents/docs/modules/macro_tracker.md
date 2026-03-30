# macro_tracker

Schema: `macro_tracker` | Automation contract: ✅

Módulo de seguimiento de macronutrientes. Permite registrar entradas de diario con alimentos, buscar productos por código de barras vía Open Food Facts, y gestionar objetivos nutricionales por usuario.

## Models

| Model | Table | Descripción |
|-------|-------|-------------|
| `DiaryEntry` | `macro_tracker.diary_entries` | Entrada de diario (comida registrada) |
| `Product` | `macro_tracker.products` | Producto/alimento (local, cacheado de OFF) |
| `UserGoal` | `macro_tracker.user_goals` | Objetivo nutricional del usuario (uno por usuario) |

## User Relationships

```python
user.diary_entries  # List[DiaryEntry]
user.user_goal      # UserGoal  (uselist=False — relación uno a uno)
```

## Key Business Logic

- `UserGoal` es una relación `uselist=False` — cada usuario tiene máximo un objetivo.
- Los productos se buscan en **Open Food Facts** por código de barras y se cachean localmente.
- `OpenFoodFactsClient` usa `httpx` (async) con User-Agent personalizado.

## External Dependencies

- **Open Food Facts API** — `OFF_BASE_URL` en `.env` (default: `https://world.openfoodfacts.org`)
- No requiere API key

> **Nota Railway:** `manifest.get_settings()` usa `os.environ` como fuente primaria. Ver patrón en `patterns.md`.

## Structure

```
macro_tracker/
├── manifest.py           ← incluye get_settings() para OFF_BASE_URL
├── models.py
├── diary_entry.py        ← modelo DiaryEntry
├── product.py            ← modelo Product
├── user_goal.py          ← modelo UserGoal
├── macro_schema.py
├── macro_router.py
├── openfoodfacts_client.py ← cliente HTTP a OFF API
├── automation_registry.py  ← registra triggers y acciones
├── automation_handlers.py  ← implementaciones de handlers
├── automation_dispatcher.py ← conecta eventos con el motor
├── scheduler_service.py    ← jobs APScheduler
├── services/
│   ├── diary_service.py  ← hooks dispatcher en add_entry() y upsert_goals()
│   ├── food_service.py   ← integra con openfoodfacts_client
│   └── stats_service.py
├── enums/
├── exceptions/
├── handlers/
└── tests/
```

## Automation Contract Implementation

### Triggers registrados

| trigger_ref | Cuándo dispara | Cómo se detecta |
|-------------|---------------|-----------------|
| `macro_tracker.meal_logged` | Al registrar una comida | Hook en `diary_service.add_entry()` tras eager-load |
| `macro_tracker.daily_macro_threshold` | Al superar/bajar de % del objetivo diario de un macro | Hook en `diary_service.add_entry()`; dedup por `(user_id, date, macro, direction)` |
| `macro_tracker.goal_updated` | Al actualizar los objetivos nutricionales | Hook en `diary_service.upsert_goals()` tras commit; snapshot previo para `changed_fields` |
| `macro_tracker.no_entry_logged_today` | Si no hay entradas hoy a cierta hora UTC | Job horario del scheduler; dedup por `(user_id, "YYYY-MM-DD")` |
| `macro_tracker.logging_streak` | Al alcanzar exactamente N días consecutivos | Job diario 00:05 UTC; coincidencia exacta (no >=); dedup por `(user_id, streak_days, "YYYY-MM-DD")` |

### Acciones registradas

| action_ref | Qué hace |
|------------|----------|
| `macro_tracker.get_daily_summary` | Resumen de macros del día con totales, objetivos y comidas agrupadas (`date_offset`) |
| `macro_tracker.get_weekly_stats` | Estadísticas semana Mon–Dom: días registrados, consistencia, medias, top 5 productos (`week_offset`) |
| `macro_tracker.get_goal_progress` | Progreso actual del día vs objetivos: goal/actual/remaining/pct por macro |
| `macro_tracker.log_meal` | Registra una comida con `skip_dispatch=True` (evita doble-dispatch) |
| `macro_tracker.get_top_products` | Productos más usados en N días, limitado a max 10 |

### Scheduler

`scheduler_service.py` registra dos jobs vía APScheduler, arrancados en `startup_event` desde `main.py`:

| Job | Frecuencia | Qué hace |
|-----|-----------|----------|
| `job_check_no_entry_today` | Horaria | Por cada automation activa, comprueba hora UTC >= check_hour y ausencia de entradas hoy |
| `job_check_logging_streak` | Diaria 00:05 UTC | Calcula racha desde ayer; lookback limitado a streak_days+1 días |

### Notas técnicas

- `diary_service.add_entry()` acepta `skip_dispatch: bool = False` — se usa en `action_log_meal` para evitar que una acción vuelva a disparar triggers.
- `upsert_goals()` toma snapshot de `UserGoal` ANTES de `_get_or_create_goal()` — si se llamara después, se perdería la información de primera creación (`old_snapshot=None`).
- `daily_macro_threshold` dedup vive en `_macro_threshold_cache` (set module-level en `automation_dispatcher.py`).
- Streak computation usa AYER como referencia (el job corre a 00:05 UTC cuando hoy puede estar incompleto).

### Tests

No llamar `job_check_*()` directamente en tests — usan `SessionLocal()` apuntando al DB de dev (5432). Llamar `dispatcher.on_*()` con la sesión de test.

Ver implementación completa:
- `backend/app/modules/macro_tracker/automation_registry.py`
- `backend/app/modules/macro_tracker/automation_handlers.py`
- `backend/app/modules/macro_tracker/automation_dispatcher.py`
- `backend/app/modules/macro_tracker/scheduler_service.py`
