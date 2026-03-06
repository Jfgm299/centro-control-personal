from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from .set import SetResponse
from ..enums import GymSetType


class ExerciseCreate(BaseModel):
    name:          str       = Field(..., min_length=1)
    exercise_type: GymSetType
    muscle_groups: List[str] = Field(default_factory=list)
    catalog_id:    Optional[int] = None
    notes:         Optional[str] = None


class ExerciseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:            int
    workout_id:    int
    name:          str
    exercise_type: GymSetType
    muscle_groups: List[str] = []
    catalog_id:    Optional[int]
    order:         int
    notes:         Optional[str]
    created_at:    datetime


class ExerciseDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:            int
    workout_id:    int
    name:          str
    exercise_type: GymSetType
    muscle_groups: List[str] = []
    catalog_id:    Optional[int]
    order:         int
    notes:         Optional[str]
    created_at:    datetime
    sets:          List[SetResponse] = []