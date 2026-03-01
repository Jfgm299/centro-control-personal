from pydantic import BaseModel, field_validator, model_validator, ConfigDict
from datetime import date, datetime
from typing import Optional


class TripCreate(BaseModel):
    title:        str
    destination:  str
    country_code: Optional[str]  = None
    lat:          Optional[float] = None
    lon:          Optional[float] = None
    start_date:   Optional[date]  = None
    end_date:     Optional[date]  = None
    description:  Optional[str]  = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El título no puede estar vacío")
        return v

    @field_validator("lat")
    @classmethod
    def validate_lat(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (-90 <= v <= 90):
            raise ValueError("La latitud debe estar entre -90 y 90")
        return v

    @field_validator("lon")
    @classmethod
    def validate_lon(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (-180 <= v <= 180):
            raise ValueError("La longitud debe estar entre -180 y 180")
        return v

    @model_validator(mode="after")
    def validate_dates(self) -> "TripCreate":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date debe ser posterior o igual a start_date")
        return self


class TripUpdate(BaseModel):
    title:        Optional[str]   = None
    destination:  Optional[str]   = None
    country_code: Optional[str]   = None
    lat:          Optional[float] = None
    lon:          Optional[float] = None
    start_date:   Optional[date]  = None
    end_date:     Optional[date]  = None
    description:  Optional[str]   = None

    @field_validator("lat")
    @classmethod
    def validate_lat(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (-90 <= v <= 90):
            raise ValueError("La latitud debe estar entre -90 y 90")
        return v

    @field_validator("lon")
    @classmethod
    def validate_lon(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (-180 <= v <= 180):
            raise ValueError("La longitud debe estar entre -180 y 180")
        return v


class TripResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:              int
    user_id:         int
    title:           str
    destination:     str
    country_code:    Optional[str]
    lat:             Optional[float]
    lon:             Optional[float]
    start_date:      Optional[date]
    end_date:        Optional[date]
    description:     Optional[str]
    cover_photo_url: Optional[str]
    created_at:      datetime
    updated_at:      Optional[datetime]


class TripMapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:              int
    title:           str
    destination:     str
    country_code:    Optional[str]
    lat:             float
    lon:             float
    cover_photo_url: Optional[str]
    start_date:      Optional[date]
    end_date:        Optional[date]