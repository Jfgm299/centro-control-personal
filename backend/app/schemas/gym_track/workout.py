from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from ...enums import MuscleGroupCategory
from .exercise import ExerciseDetailResponse

class WorkoutCreate(BaseModel):
    muscle_groups: List[MuscleGroupCategory] = Field(
        ...,
        min_items=1,
        description= 'Muscle groups working today?'
    )
    notes: Optional[str] = None

class WorkoutEnd(BaseModel):
    notes: Optional[str] = None

class WorkoutResponse(BaseModel):
    '''Simple workout response (without exercises nor sets)'''
    id: int
    started_at: datetime
    ended_at: Optional[datetime]
    duration_minutes: Optional[int]
    total_exercises: Optional[int]
    total_sets: Optional[int]
    notes: Optional[str]

    class Config:
        from_attributes = True


#Need to import other schemas, add later
class WorkoutDetailResponse(BaseModel):
    """Con ejercicios y sets incluidos"""
    id: int
    started_at: datetime
    ended_at: Optional[datetime]
    duration_minutes: Optional[int]
    muscle_groups: List[str]
    total_exercises: Optional[int]
    total_sets: Optional[int]
    notes: Optional[str]
    exercises: List[ExerciseDetailResponse] = []  # ← Aquí los incluyes
    
    class Config:
        from_attributes = True