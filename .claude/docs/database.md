# Database

## Multi-Schema Strategy

Cada módulo vive en su propio PostgreSQL schema. Esto aísla las tablas y permite que los módulos sean completamente independientes entre sí.

```
PostgreSQL
├── core              ← solo la tabla "users"
├── gym_tracker       ← workouts, exercises, sets, ...
├── expenses_tracker  ← expenses, categories, ...
├── macro_tracker     ← meals, food_items, ...
├── flights_tracker   ← flights, airports, ...
├── travels_tracker   ← trips, photos, ...
├── calendar_tracker  ← events, reminders, categories, ...
└── automations       ← automations, nodes, executions, ...
```

Todos los modelos usan `__table_args__ = {'schema': SCHEMA_NAME, 'extend_existing': True}`.
FK cross-schema se referencian explícitamente: `ForeignKey('core.users.id', ondelete='CASCADE')`.

## Docker Databases

| Servicio | Base de datos | Puerto |
|----------|---------------|--------|
| `db`     | dev           | 5432   |
| `db_test`| test          | 5433   |

## Alembic: Cómo se Crean los Schemas

`alembic/env.py` crea los schemas automáticamente antes de correr las migraciones:

```python
connection.execute(text("CREATE SCHEMA IF NOT EXISTS core"))
for schema in get_all_schemas():  # llama a module_loader.get_all_schemas()
    connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
connection.commit()
```

Esto significa que **nunca hay que crear schemas manualmente**. Al añadir un módulo nuevo con `SCHEMA_NAME` en su `manifest.py`, el schema aparece al correr `alembic upgrade head`.

## Comandos de Migración

```bash
# Aplicar todas las migraciones pendientes
docker-compose exec api alembic upgrade head

# Generar nueva migración (autogenerate detecta cambios en los modelos)
docker-compose exec api alembic revision --autogenerate -m "descripcion_breve"

# Ver historial
docker-compose exec api alembic history

# Ver estado actual
docker-compose exec api alembic current
```

## Naming Convention para Migraciones

```
<descripcion_breve_snake_case>
```

Ejemplos de lo que hay en el proyecto:
- `initial_schema`
- `add_calendar_tracker`
- `add_automations_engine`
- `add_calendar_sync_tables`
- `refactor_exercises`

Evitar nombres como `fix_X` a menos que sea realmente una corrección de una migración anterior.

## Anti-Pattern: Cambios Manuales en BD

**Qué pasó con `gymsettype`:** Se hizo un cambio manual en la BD de staging (ALTER TYPE o similar) sin pasar por Alembic. Cuando se corrió `alembic upgrade head` en staging, la migración real intentó aplicar el mismo cambio y falló por conflicto. La solución fue crear una migración vacía (`no-op`) para avanzar el head de Alembic sin tocar la BD:

```python
# 787b241dff5d_fix_gym_type_enum.py
def upgrade() -> None:
    pass  # ya aplicado manualmente — solo avanzar el revision head

def downgrade() -> None:
    pass
```

**Regla:** Nunca modificar la BD directamente en staging/producción. Todo cambio de schema va por migración Alembic.

## Verification Protocol Antes de Hacer Deploy

1. Generar migración en local: `alembic revision --autogenerate -m "..."`
2. Revisar el archivo generado — confirmar que solo toca las tablas esperadas
3. Aplicar en local: `alembic upgrade head`
4. Correr tests: `docker-compose exec api pytest`
5. Si pasa, hacer deploy — la migración corre automáticamente en staging/prod al arrancar
