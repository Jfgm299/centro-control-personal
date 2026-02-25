from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from ...enums import GymSetType

class SetCreateWeightReps(BaseModel):
    set_type: GymSetType = 'Weight_reps'
    weight_kg: float = Field(..., ge=0)
    reps: int = Field(..., gt=0)
    rpe: Optional[int] = Field(..., ge=1, le=10)
    notes: Optional[str] = None

class SetCreateCardio(BaseModel):
    set_type: GymSetType = 'Weight_reps'
    speed_kmh: float = Field(..., gt=0)
    incline_percent: float = Field(..., ge=0, le=100)
    duration_seconds: int = Field(..., gt=0)
    rpe: Optional[int] = Field(..., ge=1, le=10)
    notes: Optional[str] = None

class SetResponse(BaseModel):
    id: int
    exercise_id: int
    set_number: int
    set_type: str
    
    # Weight/Reps
    weight_kg: Optional[float]
    reps: Optional[int]
    
    # Cardio
    speed_kmh: Optional[float]
    incline_percent: Optional[float]
    duration_seconds: Optional[int]
    
    # Common
    rpe: Optional[int]
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True