from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from .set import SetResponse
from ...enums import GymSetType

class ExerciseCreate(BaseModel):
    name: str = Field(..., min_length=1, description='Name of the exercise')
    exercise_type: GymSetType
    notes: Optional[str] = None

class ExerciseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workout_id: int
    name: str
    exercise_type: GymSetType
    order: int
    notes: Optional[str]
    created_at: datetime

class ExerciseDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Con los sets incluidos"""
    id: int
    workout_id: int
    name: str
    exercise_type: GymSetType
    order: int
    notes: Optional[str]
    created_at: datetime
    sets: List[SetResponse] = []

