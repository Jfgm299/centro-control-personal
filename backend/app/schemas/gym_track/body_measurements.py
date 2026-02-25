# schemas/gym_track/body_measurement.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class BodyMeasurementCreate(BaseModel):
    weight_kg: float = Field(..., gt=0, description="Weight in kg")
    body_fat_percent: Optional[float] = Field(None, ge=0, le=100, description="Percentage of body fat")
    notes: Optional[str] = None


class BodyMeasurementResponse(BaseModel):
    id: int
    measured_at: datetime
    weight_kg: float
    body_fat_percent: Optional[float]
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True