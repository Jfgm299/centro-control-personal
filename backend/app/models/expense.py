from sqlalchemy import Column, Integer, Float, String, DateTime, Enum
from sqlalchemy.sql import func
from ..database import Base
from ..enums import ExpenseCategory


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    account = Column(Enum(ExpenseCategory), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    

