from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class SetCreate(BaseModel):
    weight_kg: Optional[float] = Field(None, ge=0)
    reps: Optional[int] = Field(None, gt=0)
    speed_kmh: Optional[float] = Field(None, gt=0)
    incline_percent: Optional[float] = Field(None, ge=0, le=100)
    duration_seconds: Optional[int] = Field(None, gt=0)
    rpe: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = None

class SetResponse(BaseModel):
    id: int
    exercise_id: int
    set_number: int
    
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