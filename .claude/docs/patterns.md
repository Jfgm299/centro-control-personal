# Patterns & Conventions

Reference implementation: `backend/app/modules/gym_tracker/`

---

## Model Convention

```python
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Workout(Base):
    __tablename__ = 'workouts'
    __table_args__ = {'schema': 'gym_tracker', 'extend_existing': True}

    id      = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('core.users.id', ondelete='CASCADE'), nullable=False)
    # ... rest of columns

    user = relationship("User", back_populates="workouts")
```

**Reglas:**
- `__table_args__` siempre con `schema=SCHEMA_NAME` y `extend_existing=True`
- FK a usuario: `ForeignKey('core.users.id', ondelete='CASCADE')`
- La relación `user` siempre con `back_populates` al nombre declarado en `manifest.py`
- Un archivo por modelo en `models/` — `models.py` en la raíz del módulo solo re-exporta

---

## Schema Convention (Pydantic v2)

```python
from pydantic import BaseModel, ConfigDict
from typing import Optional

class WorkoutCreate(BaseModel):
    notes: Optional[str] = None

class WorkoutResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # permite leer desde ORM

    id:         int
    started_at: datetime
    notes:      Optional[str]
```

**Reglas:**
- Separar en `Create`, `Update`, `Response` (y `DetailResponse` si incluye relaciones)
- Solo los schemas de respuesta necesitan `model_config = ConfigDict(from_attributes=True)`
- No poner `from_attributes=True` en schemas de entrada (Create/Update)

---

## Service Convention

```python
class WorkoutService:

    def start_workout(self, db: Session, data: WorkoutCreate, user_id: int) -> dict:
        # 1. validar ownership / estado previo
        # 2. crear ORM object, db.add(), db.commit(), db.refresh()
        # 3. devolver dict (no el ORM object directamente)
        return self._workout_to_dict(workout)

workout_service = WorkoutService()  # singleton al final del archivo
```

**Reglas:**
- Clases, no funciones sueltas
- Singleton al final del archivo (`my_service = MyService()`)
- Siempre recibir `user_id: int` y filtrar por él — nunca confiar en que el objeto ya pertenece al usuario
- Devolver `dict` o Pydantic model — nunca el ORM object raw (evita lazy-loading fuera de sesión)
- Lanzar excepciones del módulo (`raise WorkoutNotFoundError(workout_id)`) — nunca `HTTPException`

---

## Router Convention

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.auth.user import User

router = APIRouter(prefix="/workouts", tags=["Workouts"])

@router.post("/", response_model=WorkoutResponse, status_code=201)
def start_workout(
    data: WorkoutCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return workout_service.start_workout(db, data, user_id=user.id)
```

**Reglas:**
- Routers finos — solo extraer parámetros y delegar al service
- Siempre `response_model` y `status_code` explícitos
- Tags en formato `"My Tag"` (deben coincidir con `TAGS` en `__init__.py`)
- `prefix` en el router, no en `include_router`

---

## Exception Convention

**Capa 1 — Base (`app/core/exeptions.py`):**
```python
class AppException(Exception):
    def __init__(self, message: str, status_code: int = 500): ...

class NotYoursError(AppException):  # 403 genérico de ownership
    def __init__(self, resource: str = "recurso"): ...
```

**Capa 2 — Excepciones del módulo (`exceptions/module_exceptions.py`):**
```python
from app.core.exeptions import AppException

class WorkoutNotFoundError(AppException):
    def __init__(self, workout_id: int):
        super().__init__(message=f"Workout {workout_id} not found", status_code=404)
```

**Capa 3 — Handlers (`handlers/module_handlers.py`):**
```python
async def workout_not_found_handler(request: Request, exc: WorkoutNotFoundError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

MODULE_EXCEPTION_HANDLERS = {
    WorkoutNotFoundError: workout_not_found_handler,
    ...
}
```

**Capa 4 — Registro (`handlers/__init__.py`):**
```python
from app.core.handlers import CORE_EXCEPTION_HANDLERS

def register_exception_handlers(app):
    all_handlers = {**CORE_EXCEPTION_HANDLERS, **MODULE_EXCEPTION_HANDLERS}
    for exc_class, handler in all_handlers.items():
        app.add_exception_handler(exc_class, handler)
```

---

## Automation Handler Convention

**Trigger handler** — indica si la condición se cumplió:
```python
def handle_something(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    entity_id = payload.get("entity_id")
    if not entity_id:
        return {"matched": False, "reason": "no entity_id in payload"}

    entity = db.query(MyModel).filter(
        MyModel.id == entity_id,
        MyModel.user_id == user_id,
    ).first()
    if not entity:
        return {"matched": False, "reason": f"entity {entity_id} not found"}

    # filtros de config...
    return {"matched": True, "entity": entity_to_dict(entity)}
```

**Action handler** — ejecuta una operación:
```python
def action_create_something(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    title = config.get("title", "Default")
    obj = MyModel(title=title, user_id=user_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return {"done": True, "item": obj_to_dict(obj)}
```
