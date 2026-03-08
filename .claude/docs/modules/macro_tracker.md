# macro_tracker

Schema: `macro_tracker` | Automation contract: ❌

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
├── services/
│   ├── diary_service.py
│   ├── food_service.py   ← integra con openfoodfacts_client
│   └── stats_service.py
├── enums/
├── exceptions/
├── handlers/
└── tests/
```
