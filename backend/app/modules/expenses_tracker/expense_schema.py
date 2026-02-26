from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional
from .enums import ExpenseCategory

class ExpenseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    quantity: float = Field(..., gt=0, description='Amount spent')
    account: ExpenseCategory

    @field_validator('name')
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()

class ExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    quantity: float
    account: str
    created_at: datetime
    updated_at: Optional[datetime]

class ExpenseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    quantity: Optional[float] = Field(None, gt=0)
    account: Optional[ExpenseCategory] = None