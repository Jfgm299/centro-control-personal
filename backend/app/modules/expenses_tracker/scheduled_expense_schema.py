from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from .scheduled_expense_model import ScheduledFrequency, ScheduledCategory
from .enums import ExpenseCategory


class ScheduledExpenseCreate(BaseModel):
    name:               str              = Field(..., min_length=1, max_length=100)
    amount:             float            = Field(..., gt=0)
    account:            ExpenseCategory
    frequency:          ScheduledFrequency = ScheduledFrequency.MONTHLY
    category:           ScheduledCategory  = ScheduledCategory.SUBSCRIPTION
    next_payment_date:  Optional[date]   = None
    is_active:          bool             = True
    icon:               Optional[str]    = None
    color:              Optional[str]    = None
    notes:              Optional[str]    = None
    custom_days:        Optional[int]    = Field(None, gt=0)


class ScheduledExpenseUpdate(BaseModel):
    name:               Optional[str]              = Field(None, min_length=1, max_length=100)
    amount:             Optional[float]            = Field(None, gt=0)
    account:            Optional[ExpenseCategory]  = None
    frequency:          Optional[ScheduledFrequency] = None
    category:           Optional[ScheduledCategory]  = None
    next_payment_date:  Optional[date]             = None
    is_active:          Optional[bool]             = None
    icon:               Optional[str]              = None
    color:              Optional[str]              = None
    notes:              Optional[str]              = None
    custom_days:        Optional[int]              = Field(None, gt=0)


class ScheduledExpenseResponse(BaseModel):
    id:                 int
    name:               str
    amount:             float
    account:            str
    frequency:          str
    category:           str
    next_payment_date:  Optional[date]
    is_active:          bool
    icon:               Optional[str]
    color:              Optional[str]
    notes:              Optional[str]
    custom_days:        Optional[int]
    created_at:         datetime
    updated_at:         Optional[datetime]

    class Config:
        from_attributes = True