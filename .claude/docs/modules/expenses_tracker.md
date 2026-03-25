# expenses_tracker

Schema: `expenses_tracker` | Automation contract: ❌

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
├── expense.py               ← modelo Expense
├── scheduled_expense_model.py ← modelo ScheduledExpense
├── expense_schema.py
├── scheduled_expense_schema.py
├── expense_service.py
├── scheduled_expense_service.py
├── expenses_router.py
├── enums/
└── tests/
```

## External Dependencies

Ninguna — módulo completamente local.
