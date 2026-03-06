# ── exercise_catalog_service.py ───────────────────────────────────────────────
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.exercise_catalog import ExerciseCatalog
from pydantic import BaseModel, ConfigDict
from ..enums import GymSetType


class CatalogExerciseCreate(BaseModel):
    name:          str
    exercise_type: GymSetType
    muscle_groups: List[str]


class CatalogExerciseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:            int
    name:          str
    exercise_type: GymSetType
    muscle_groups: List[str]
    is_custom:     bool


class ExerciseCatalogService:

    def get_all(self, db: Session, user_id: int) -> List[ExerciseCatalog]:
        """Devuelve ejercicios globales + custom del usuario."""
        return (
            db.query(ExerciseCatalog)
            .filter(
                (ExerciseCatalog.user_id == None) |
                (ExerciseCatalog.user_id == user_id)
            )
            .order_by(ExerciseCatalog.name)
            .all()
        )

    def create_custom(self, db: Session, data: CatalogExerciseCreate, user_id: int) -> ExerciseCatalog:
        obj = ExerciseCatalog(
            name=data.name.strip().title(),
            exercise_type=data.exercise_type,
            muscle_groups=data.muscle_groups,
            is_custom=True,
            user_id=user_id,
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def delete_custom(self, db: Session, catalog_id: int, user_id: int) -> bool:
        obj = db.query(ExerciseCatalog).filter(
            ExerciseCatalog.id == catalog_id,
            ExerciseCatalog.user_id == user_id,
            ExerciseCatalog.is_custom == True,
        ).first()
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True


exercise_catalog_service = ExerciseCatalogService()