# 💸 Expenses Tracker

Módulo de control y seguimiento de gastos personales.

## ¿Qué hace?

Permite registrar, consultar, actualizar y eliminar gastos categorizados por cuenta. Cada gasto tiene un nombre, importe, categoría y fecha de creación automática.

## Instalación

Añade el módulo a `INSTALLED_MODULES` en tu configuración:

```python
# core/config.py
INSTALLED_MODULES = [
    "expenses_tracker",
    # otros módulos...
]
```

Para desactivarlo, comenta o elimina la línea. El resto de módulos no se verá afectado.

## Endpoints

Base URL: `/api/v1/expenses`

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/` | Listar todos los gastos |
| `POST` | `/` | Crear un nuevo gasto |
| `GET` | `/{expense_id}` | Obtener un gasto por ID |
| `PATCH` | `/{expense_id}` | Actualizar un gasto |
| `DELETE` | `/{expense_id}` | Eliminar un gasto |

## Modelos

### Expense

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `id` | `int` | auto | Identificador único |
| `name` | `str` | ✅ | Nombre del gasto (max 100 chars) |
| `quantity` | `float` | ✅ | Importe (debe ser > 0) |
| `account` | `ExpenseCategory` | ✅ | Cuenta o categoría del gasto |
| `created_at` | `datetime` | auto | Fecha de creación |
| `updated_at` | `datetime` | auto | Última actualización |

### ExpenseCategory (enum)

```
Imagin · BBVA · Efectivo · ...
```

> Consulta `enums/expense_category.py` para ver todos los valores disponibles.

## Ejemplos de uso

### Crear un gasto

```http
POST /api/v1/expenses/
Content-Type: application/json

{
  "name": "Supermercado",
  "quantity": 45.50,
  "account": "Imagin"
}
```

### Respuesta

```json
{
  "id": 1,
  "name": "Supermercado",
  "quantity": 45.50,
  "account": "Imagin",
  "created_at": "2026-02-26T12:00:00",
  "updated_at": null
}
```

### Actualizar un gasto

```http
PATCH /api/v1/expenses/1
Content-Type: application/json

{
  "quantity": 48.00
}
```

## Estructura del módulo

```
expenses_tracker/
    __init__.py         # Exporta router
    expenses_router.py  # Endpoints
    expense_service.py  # Lógica de negocio
    expense_schema.py   # Schemas Pydantic
    expense.py          # Modelo SQLAlchemy
    enums/
        expense_category.py
    tests/
        __init__.py
        test_expenses.py
```

## Tests

```bash
# Ejecutar solo los tests de este módulo
docker-compose exec api pytest app/modules/expenses_tracker/tests/ -v
```

## Dependencias

- No depende de ningún otro módulo
- Requiere: `app.core.database` (Base, get_db)
- Requiere: `app.core.exceptions` (AppException)