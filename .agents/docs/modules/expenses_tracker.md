# expenses_tracker

Schema: `expenses_tracker` | Automation contract: ✅

Módulo de seguimiento de gastos. Soporta gastos puntuales y gastos programados (suscripciones, pagos recurrentes).

## Models

| Model | Table | Descripción |
|-------|-------|-------------|
| `Expense` | `expenses_tracker.expenses` | Gasto individual puntual |
| `ScheduledExpense` | `expenses_tracker.scheduled_expenses` | Gasto programado/recurrente |

**Nota estructural:** Este módulo tiene una estructura más plana que gym_tracker — los archivos de modelo, schema, service y router están directamente en la raíz del módulo (sin subdirectorios), lo que refleja su menor complejidad.

## User Relationships

```python
user.expenses            # List[Expense]
user.scheduled_expenses  # List[ScheduledExpense]
```

## Key Business Logic

- `ScheduledExpense` tiene frecuencias: `WEEKLY`, `MONTHLY`, `YEARLY`, `CUSTOM`
- Categorías de gasto programado: `SUBSCRIPTION`, `ONE_TIME`
- Las categorías de gasto puntual se gestionan con un enum `ExpenseCategory`
- **Auto-conversión de gastos vencidos:** Al listar gastos programados (`get_all`), el servicio detecta automáticamente los que tienen `next_payment_date <= today` y los convierte en gastos reales (`Expense`):
  - `ONE_TIME` — crea un `Expense` y desactiva el gasto programado (`is_active = False`)
  - `SUBSCRIPTION` — crea un `Expense` por cada período vencido y avanza `next_payment_date` según la frecuencia hasta que sea futura

## Structure

```
expenses_tracker/
├── manifest.py
├── models.py
├── expense.py                    ← modelo Expense
├── scheduled_expense_model.py    ← modelo ScheduledExpense
├── expense_schema.py
├── scheduled_expense_schema.py
├── expense_service.py            ← hook para large_expense_created
├── scheduled_expense_service.py  ← hook para subscription_converted
├── expenses_router.py
├── automation_registry.py        ← registra triggers y acciones
├── automation_handlers.py        ← implementaciones de handlers
├── automation_dispatcher.py      ← conecta eventos con el motor
├── scheduler_service.py          ← jobs diarios (APScheduler)
├── enums/
└── tests/
```

## External Dependencies

Ninguna — módulo completamente local.

## Automation Contract Implementation

### Triggers registrados

| trigger_ref | Cuándo dispara | Cómo se detecta |
|-------------|---------------|-----------------|
| `expenses_tracker.large_expense_created` | Al crear un gasto que supera `min_amount` | Hook en `expense_service.create_expense()` |
| `expenses_tracker.monthly_budget_exceeded` | Cuando el total mensual del usuario supera `limit` | Job diario del scheduler |
| `expenses_tracker.subscription_due_soon` | Cuando una suscripción vence en los próximos `days_ahead` días | Job diario del scheduler |
| `expenses_tracker.subscription_converted` | Cuando una suscripción vencida se convierte automáticamente en gasto | Hook en `scheduled_expense_service.get_all()` |

### Acciones registradas

| action_ref | Qué hace |
|------------|----------|
| `expenses_tracker.create_expense` | Crea un gasto puntual con nombre, importe y cuenta |
| `expenses_tracker.get_monthly_summary` | Devuelve totales mensuales agrupados por cuenta (`month_offset` 0=actual, -1=anterior) |
| `expenses_tracker.get_upcoming_subscriptions` | Lista suscripciones activas con vencimiento en los próximos N días |

### Scheduler

`scheduler_service.py` registra dos jobs diarios vía APScheduler, arrancados en `startup_event` desde `main.py`:

| Job | Frecuencia | Qué hace |
|-----|-----------|----------|
| `job_check_subscription_due_soon` | Diaria | Detecta suscripciones con `next_payment_date` entre mañana y +30 días; deduplicación por `(scheduled_id, due_date)` por día |
| `job_check_monthly_budget` | Diaria | Itera automations activas con `trigger_ref=expenses_tracker.monthly_budget_exceeded`, calcula total mensual del usuario y dispara si supera el límite; deduplicación por `(user_id, "YYYY-MM")` |

Ambos jobs usan deduplicación en memoria para evitar disparar el mismo trigger más de una vez por día/mes para el mismo objeto.

### Dispatcher

`automation_dispatcher.py` contiene `ExpensesAutomationDispatcher` — conecta los eventos del módulo (hooks de servicio y jobs del scheduler) con el motor de automatizaciones.

Ver implementación completa:
- `backend/app/modules/expenses_tracker/automation_registry.py`
- `backend/app/modules/expenses_tracker/automation_dispatcher.py`
- `backend/app/modules/expenses_tracker/automation_handlers.py`
