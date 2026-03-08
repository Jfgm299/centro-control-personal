Crea la estructura completa de un módulo nuevo. Solicita el nombre del módulo si no se proporcionó como argumento.

## Convenciones de nombre
- Snake case: `my_module`
- Schema PostgreSQL: igual que el nombre del módulo (salvo excepciones como `automations_engine` → `automations`)

## Estructura a crear

```
backend/app/modules/<module_name>/
├── __init__.py              ← exports: router, register_handlers, TAGS, TAG_GROUP
├── manifest.py              ← SCHEMA_NAME, USER_RELATIONSHIPS, get_settings() (si necesario)
├── models.py                ← re-exporta modelos para alembic
├── models/
│   └── my_entity.py         ← modelo SQLAlchemy con schema correcto
├── schemas/
│   └── my_entity.py         ← Create / Response schemas (Pydantic v2)
├── services/
│   └── my_entity_service.py ← clase-based singleton
├── routers/
│   └── my_entity_router.py  ← APIRouter fino
├── exceptions/
│   └── __init__.py          ← excepciones heredando de AppException
├── handlers/
│   └── __init__.py          ← register_exception_handlers(app)
└── tests/
    ├── __init__.py
    └── conftest.py          ← fixtures de datos (recursos vía API, no ORM directo)
```

## Checklist de implementación

1. **`manifest.py`** — definir `SCHEMA_NAME` y `USER_RELATIONSHIPS`
2. **Modelo** — `__table_args__ = {'schema': SCHEMA_NAME, 'extend_existing': True}` + FK a `core.users.id`
3. **`models.py`** — re-exportar todos los modelos con `# noqa: F401`
4. **Schemas** — separar `Create`, `Update`, `Response`; solo `Response` lleva `ConfigDict(from_attributes=True)`
5. **Service** — clase con singleton al final; siempre filtrar por `user_id`; devolver `dict` o Pydantic model
6. **Router** — `prefix` y `tags` en el router; `response_model` y `status_code` explícitos
7. **Exceptions** — heredar de `AppException`; handler devuelve `JSONResponse` con `{"detail": exc.message}`
8. **`__init__.py`** — exportar `router`, `register_handlers`, `TAGS`, `TAG_GROUP`
9. **Migración** — `docker-compose exec api alembic revision --autogenerate -m "add_<module_name>"`
10. **Doc** — crear `docs/modules/<module_name>.md` y añadir fila en `docs/modules/README.md`

## Automation contract (opcional)

Si el módulo expone triggers/acciones, añadir:
- `automation_registry.py` con función `register(registry)`
- `services/automation_handlers.py` con los handlers
- (Opcional) `automation_dispatcher.py` si el módulo tiene scheduler propio

Ver `@docs/module-system.md` para el contrato completo y `calendar_tracker` como referencia.
