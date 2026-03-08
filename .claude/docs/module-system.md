# Module System

## Auto-Discovery Mechanics (`backend/app/core/module_loader.py`)

Un módulo es válido si existe en `backend/app/modules/<name>/` con un `manifest.py` que tenga `SCHEMA_NAME`.

| Función | Qué hace |
|---------|----------|
| `get_installed_modules()` | Itera `app/modules/`, filtra dirs con `manifest.py`, devuelve lista ordenada |
| `import_all_models()` | Importa `models.py` de cada módulo para registrar en `Base.metadata` |
| `get_all_schemas()` | Devuelve los `SCHEMA_NAME` de todos los módulos (usado por alembic) |
| `register_user_relationships()` | Inyecta relaciones en `User` desde `USER_RELATIONSHIPS` de cada manifest |
| `register_automation_handlers(registry)` | Busca `automation_registry.py` en cada módulo y llama `register(registry)` |

**No hay lista manual.** Copiar la carpeta de un módulo en `app/modules/` es suficiente para que todo se autodescubra.

---

## `manifest.py` Full Spec

```python
# Requerido — define el schema PostgreSQL del módulo
SCHEMA_NAME = "gym_tracker"

# Opcional — relaciones a inyectar en el modelo User
USER_RELATIONSHIPS = [
    {
        "name":          "workouts",          # atributo en User
        "target":        "Workout",           # nombre del modelo SQLAlchemy
        "back_populates": "user",             # back_populates en el modelo hijo
        "cascade":       "all, delete-orphan",# opcional, default: "all, delete-orphan"
        "uselist":       True,                # opcional, default: True
    },
]

# Opcional — para módulos con settings (env vars, etc.)
def get_settings():
    ...
```

---

## Automation Contract

### `automation_registry.py` — función `register(registry)`

Cada módulo que expone triggers/acciones crea este archivo con una función `register`:

```python
def register(registry) -> None:
    registry.register_trigger(
        module_id="my_module",
        trigger_id="something_happened",
        label="Descripción legible",
        config_schema={
            "field_name": {
                "type":     "str",          # ver tipos abajo
                "label":    "Label UI",
                "default":  "valor",        # opcional
                "optional": True,           # si no está, el campo es requerido
            },
        },
        handler="app.modules.my_module.services.handlers.handle_something",
    )

    registry.register_action(
        module_id="my_module",
        action_id="do_something",
        label="Descripción legible",
        config_schema={ ... },
        handler="app.modules.my_module.services.handlers.action_do_something",
    )
```

### `TriggerDef` / `ActionDef` (definidos en `automations_engine/core/registry.py`)

```python
@dataclass
class TriggerDef:
    ref_id:        str   # "module_id.trigger_id"
    module_id:     str
    label:         str
    config_schema: dict
    handler_path:  str   # dotted path importable

@dataclass
class ActionDef:
    ref_id:        str   # "module_id.action_id"
    module_id:     str
    label:         str
    config_schema: dict
    handler_path:  str
```

### Handler Function Signature

```python
def handle_something(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    ...
```

- `payload` — datos del evento que disparó el trigger (ej. `{"event_id": 42}`)
- `config` — configuración guardada por el usuario en la automatización
- `db` — sesión SQLAlchemy (ya abierta)
- `user_id` — ID del usuario propietario de la automatización

### `config_schema` — Tipos de Campo

| Tipo | Ejemplo |
|------|---------|
| `str` | título, descripción |
| `int` | duración, ID |
| `bool` | activar/desactivar |
| `text` | texto largo |
| `datetime` | fecha y hora exacta |
| `time` | hora del día |
| `enum[a,b,c]` | `"enum[low,medium,high,urgent]"` |
| `list[int]` | lista de IDs |
| `object` | estructura anidada |

### Return Value Conventions

**Triggers** — indican si la condición se cumplió:
```python
{"matched": True, "event": {...}}   # condición cumplida — incluir datos útiles
{"matched": False, "reason": "..."}  # condición no cumplida — el flujo se detiene
```

**Acciones** — indican si la operación se realizó:
```python
{"done": True, "item": {...}}        # acción completada
{"created": True, "item": {...}}     # variante para creaciones
{"done": False, "reason": "..."}     # acción fallida (sin lanzar excepción)
```

### `automation_dispatcher.py` — Patrón (opcional)

Archivo que conecta eventos del módulo (scheduler, hooks de servicio) con el motor de automatizaciones. Patrón recomendado:

```python
class MyModuleDispatcher:
    def _find_and_execute(self, trigger_ref, payload, user_id, db):
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.automations_engine.services.flow_executor import flow_executor
        # buscar automations con trigger_ref activas del user_id
        # crear execution, marcar running, ejecutar, marcar success/failed

    def on_something_happened(self, entity_id, user_id, db):
        self._find_and_execute(
            trigger_ref="my_module.something_happened",
            payload={"entity_id": entity_id},
            user_id=user_id,
            db=db,
        )

dispatcher = MyModuleDispatcher()  # singleton
```

Ver implementación completa: `backend/app/modules/calendar_tracker/automation_dispatcher.py`

---

## Module `__init__.py` Export Contract

```python
from fastapi import APIRouter
from .routers.my_router import router as my_router
from .handlers import register_exception_handlers as register_handlers

router = APIRouter()
router.include_router(my_router)

TAGS = [{"name": "MyTag", "description": "..."}]
TAG_GROUP = {"name": "My Module", "tags": ["MyTag"]}

__all__ = ['router', 'register_handlers', 'TAGS', 'TAG_GROUP']
```

- `router` — requerido (FastAPI router con todos los sub-routers del módulo)
- `register_handlers` — requerido (registra exception handlers en la app)
- `TAGS` — para OpenAPI/Swagger
- `TAG_GROUP` — para agrupar en ReDoc (`x-tagGroups`)
