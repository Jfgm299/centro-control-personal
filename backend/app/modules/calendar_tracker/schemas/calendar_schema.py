from __future__ import annotations
from datetime import date, datetime, time
from typing import Optional
from pydantic import BaseModel, Field, model_validator

from ..enums import ReminderStatus, ReminderPriority, RoutineExceptionAction


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY
# ══════════════════════════════════════════════════════════════════════════════

class CategoryCreate(BaseModel):
    name:                    str            = Field(..., min_length=1, max_length=100)
    color:                   Optional[str]  = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon:                    Optional[str]  = Field(None, max_length=50)
    default_enable_dnd:      bool           = False
    default_reminder_minutes:Optional[int]  = Field(None, ge=1, le=1440)


class CategoryUpdate(BaseModel):
    name:                    Optional[str]  = Field(None, min_length=1, max_length=100)
    color:                   Optional[str]  = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon:                    Optional[str]  = Field(None, max_length=50)
    default_enable_dnd:      Optional[bool] = None
    default_reminder_minutes:Optional[int]  = Field(None, ge=1, le=1440)


class CategoryResponse(BaseModel):
    id:                      int
    user_id:                 int
    name:                    str
    color:                   str
    icon:                    Optional[str]
    default_enable_dnd:      bool
    default_reminder_minutes:Optional[int]
    created_at:              datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# REMINDER
# ══════════════════════════════════════════════════════════════════════════════

class ReminderCreate(BaseModel):
    title:       str                     = Field(..., min_length=1, max_length=200)
    description: Optional[str]           = None
    category_id: Optional[int]           = None
    priority:    ReminderPriority        = ReminderPriority.MEDIUM
    due_date:    Optional[date]          = None


class ReminderUpdate(BaseModel):
    title:       Optional[str]           = Field(None, min_length=1, max_length=200)
    description: Optional[str]           = None
    category_id: Optional[int]           = None
    priority:    Optional[ReminderPriority] = None
    due_date:    Optional[date]          = None


class ReminderSchedule(BaseModel):
    """Payload para asignar un reminder a una franja horaria — crea un Event."""
    start_at:         datetime
    end_at:           datetime
    enable_dnd:       bool          = False
    reminder_minutes: Optional[int] = Field(None, ge=1, le=1440)
    color_override:   Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")

    @model_validator(mode="after")
    def end_after_start(self) -> ReminderSchedule:
        if self.end_at <= self.start_at:
            raise ValueError("end_at debe ser posterior a start_at")
        return self


class ReminderResponse(BaseModel):
    id:          int
    user_id:     int
    category_id: Optional[int]
    title:       str
    description: Optional[str]
    status:      ReminderStatus
    priority:    ReminderPriority
    due_date:    Optional[date]
    created_at:  datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# EVENT
# ══════════════════════════════════════════════════════════════════════════════

class EventCreate(BaseModel):
    title:            str            = Field(..., min_length=1, max_length=200)
    description:      Optional[str]  = None
    category_id:      Optional[int]  = None
    start_at:         datetime
    end_at:           datetime
    all_day:          bool           = False
    color_override:   Optional[str]  = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    enable_dnd:       bool           = False
    reminder_minutes: Optional[int]  = Field(None, ge=1, le=1440)

    @model_validator(mode="after")
    def end_after_start(self) -> EventCreate:
        if not self.all_day and self.end_at <= self.start_at:
            raise ValueError("end_at debe ser posterior a start_at")
        return self


class EventUpdate(BaseModel):
    title:            Optional[str]      = Field(None, min_length=1, max_length=200)
    description:      Optional[str]      = None
    category_id:      Optional[int]      = None
    start_at:         Optional[datetime] = None
    end_at:           Optional[datetime] = None
    all_day:          Optional[bool]     = None
    color_override:   Optional[str]      = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    enable_dnd:       Optional[bool]     = None
    reminder_minutes: Optional[int]      = Field(None, ge=1, le=1440)

    @model_validator(mode="after")
    def end_after_start(self) -> EventUpdate:
        if self.start_at and self.end_at and self.end_at <= self.start_at:
            raise ValueError("end_at debe ser posterior a start_at")
        return self


class EventResponse(BaseModel):
    id:               Optional[int]
    user_id:          int
    reminder_id:      Optional[int]
    routine_id:       Optional[int]
    category_id:      Optional[int]
    title:            str
    description:      Optional[str]
    start_at:         datetime
    end_at:           datetime
    all_day:          bool
    color_override:   Optional[str]
    enable_dnd:       bool
    reminder_minutes: Optional[int]
    google_event_id:  Optional[str]
    apple_event_id:   Optional[str]
    is_cancelled:     bool
    created_at:       datetime
    updated_at:       Optional[datetime]
    category:         Optional[CategoryResponse] = None

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# ROUTINE
# ══════════════════════════════════════════════════════════════════════════════

class RoutineCreate(BaseModel):
    title:            str            = Field(..., min_length=1, max_length=200)
    description:      Optional[str]  = None
    category_id:      Optional[int]  = None
    rrule:            str            = Field(..., min_length=1)
    start_time:       time
    end_time:         time
    valid_from:       date
    valid_until:      Optional[date] = None
    enable_dnd:       bool           = False
    reminder_minutes: Optional[int]  = Field(None, ge=1, le=1440)

    @model_validator(mode="after")
    def end_after_start(self) -> RoutineCreate:
        if self.end_time <= self.start_time:
            raise ValueError("end_time debe ser posterior a start_time")
        if self.valid_until and self.valid_until <= self.valid_from:
            raise ValueError("valid_until debe ser posterior a valid_from")
        return self


class RoutineUpdate(BaseModel):
    title:            Optional[str]  = Field(None, min_length=1, max_length=200)
    description:      Optional[str]  = None
    category_id:      Optional[int]  = None
    rrule:            Optional[str]  = Field(None, min_length=1)
    start_time:       Optional[time] = None
    end_time:         Optional[time] = None
    valid_from:       Optional[date] = None
    valid_until:      Optional[date] = None
    enable_dnd:       Optional[bool] = None
    reminder_minutes: Optional[int]  = Field(None, ge=1, le=1440)
    is_active:        Optional[bool] = None


class RoutineResponse(BaseModel):
    id:               int
    user_id:          int
    category_id:      Optional[int]
    title:            str
    description:      Optional[str]
    rrule:            str
    start_time:       time
    end_time:         time
    valid_from:       date
    valid_until:      Optional[date]
    enable_dnd:       bool
    reminder_minutes: Optional[int]
    is_active:        bool
    created_at:       datetime
    category:         Optional[CategoryResponse] = None

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# ROUTINE EXCEPTION
# ══════════════════════════════════════════════════════════════════════════════

class RoutineExceptionCreate(BaseModel):
    original_date:       date
    action:              RoutineExceptionAction
    new_start_at:        Optional[datetime] = None
    new_end_at:          Optional[datetime] = None
    new_title:           Optional[str]      = Field(None, min_length=1, max_length=200)
    new_enable_dnd:      Optional[bool]     = None
    new_reminder_minutes:Optional[int]      = Field(None, ge=1, le=1440)

    @model_validator(mode="after")
    def validate_modified_fields(self) -> RoutineExceptionCreate:
        if self.action == RoutineExceptionAction.MODIFIED:
            if self.new_start_at and self.new_end_at:
                if self.new_end_at <= self.new_start_at:
                    raise ValueError("new_end_at debe ser posterior a new_start_at")
        return self


class RoutineExceptionResponse(BaseModel):
    id:                  int
    routine_id:          int
    original_date:       date
    action:              RoutineExceptionAction
    new_start_at:        Optional[datetime]
    new_end_at:          Optional[datetime]
    new_title:           Optional[str]
    new_enable_dnd:      Optional[bool]
    new_reminder_minutes:Optional[int]
    created_at:          datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# FCM TOKEN
# ══════════════════════════════════════════════════════════════════════════════

class FcmTokenCreate(BaseModel):
    token:       str = Field(..., min_length=1)
    device_type: str = Field(..., pattern=r"^(ios|android|web)$")


class FcmTokenResponse(BaseModel):
    id:          int
    user_id:     int
    token:       str
    device_type: str
    created_at:  datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# QUERY HELPERS
# ══════════════════════════════════════════════════════════════════════════════

class EventRangeQuery(BaseModel):
    """Parámetros de query para listar eventos en un rango."""
    start: datetime
    end:   datetime

    @model_validator(mode="after")
    def end_after_start(self) -> EventRangeQuery:
        if self.end <= self.start:
            raise ValueError("end debe ser posterior a start")
        return self