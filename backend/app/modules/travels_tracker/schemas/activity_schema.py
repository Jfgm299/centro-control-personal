from pydantic import BaseModel, field_validator, ConfigDict
from datetime import date as Date, datetime
from typing import Optional
from ..enums.activity_category import ActivityCategory


class ActivityCreate(BaseModel):
    title:       str
    category:    Optional[ActivityCategory] = None
    description: Optional[str]  = None
    date:        Optional[Date]  = None
    lat:         Optional[float] = None
    lon:         Optional[float] = None
    rating:      Optional[int]   = None
    position:    int = 0

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 5):
            raise ValueError("El rating debe estar entre 1 y 5")
        return v


class ActivityUpdate(BaseModel):
    title:       Optional[str]              = None
    category:    Optional[ActivityCategory] = None
    description: Optional[str]             = None
    date:        Optional[Date]             = None
    lat:         Optional[float]            = None
    lon:         Optional[float]            = None
    rating:      Optional[int]              = None
    position:    Optional[int]              = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 5):
            raise ValueError("El rating debe estar entre 1 y 5")
        return v


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:          int
    trip_id:     int
    user_id:     int
    title:       str
    category:    Optional[ActivityCategory]
    description: Optional[str]
    date:        Optional[Date]
    lat:         Optional[float]
    lon:         Optional[float]
    rating:      Optional[int]
    position:    int
    created_at:  datetime