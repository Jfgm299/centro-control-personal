# schemas/gym_track/body_measurement.py
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class BodyMeasurementCreate(BaseModel):
    weight_kg: float = Field(..., gt=0, description="Weight in kg")
    body_fat_percentage: Optional[float] = Field(None, ge=0, le=100, description="Percentage of body fat")
    notes: Optional[str] = None


class BodyMeasurementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    weight_kg: float
    body_fat_percentage: Optional[float]
    notes: Optional[str]
    created_at: datetime