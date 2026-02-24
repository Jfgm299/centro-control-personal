from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from ..enums import ExpenseCategory

class ExpenseCreate(BaseModel):
    name: str = Field(...,min_length=1, max_length=100)
    quantity: float = Field(..., gt=0, description='Amount spent')
    account: ExpenseCategory

class ExpenseResponse(BaseModel):
    id: int
    name: str
    quantity: float
    account: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class ExpenseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length = 1, max_length = 100)
    quantity: Optional[float] = Field(None, gt=0)
    account: Optional[ExpenseCategory] = None

    