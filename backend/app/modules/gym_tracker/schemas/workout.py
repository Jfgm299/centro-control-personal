# ── workout.py ────────────────────────────────────────────────────────────────
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from ..enums import MuscleGroupCategory
from .exercise import ExerciseDetailResponse


class WorkoutCreate(BaseModel):
    # muscle_groups ya no es obligatorio — se computa automáticamente al acabar
    muscle_groups: List[MuscleGroupCategory] = Field(default_factory=list)
    notes: Optional[str] = None


class WorkoutEnd(BaseModel):
    notes: Optional[str] = None


class WorkoutResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    started_at: datetime
    ended_at: Optional[datetime]
    duration_minutes: Optional[int]
    total_exercises: Optional[int]
    total_sets: Optional[int]
    notes: Optional[str]
    muscle_groups: List[str] = []


class WorkoutDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    started_at: datetime
    ended_at: Optional[datetime]
    duration_minutes: Optional[int]
    muscle_groups: List[str]
    total_exercises: Optional[int]
    total_sets: Optional[int]
    notes: Optional[str]
    exercises: List[ExerciseDetailResponse] = []