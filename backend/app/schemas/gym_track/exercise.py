from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from .set import SetResponse
from ...enums import GymSetType

class ExerciseCreate(BaseModel):
    name: str = Field(..., min_length=1, description='Name of the exercise')
    exercise_type: GymSetType
    notes: Optional[str] = None

class ExerciseResponse(BaseModel):
    id: int
    workout_id: int
    name: str
    exercise_type: GymSetType
    order: int
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class ExerciseDetailResponse(BaseModel):
    """Con los sets incluidos"""
    id: int
    workout_id: int
    name: str
    exercise_type: GymSetType
    order: int
    notes: Optional[str]
    created_at: datetime
    sets: List[SetResponse] = []  # ← Aquí los incluyes
    
    class Config:
        from_attributes = True

