from sqlalchemy import Column, Integer, Float, String, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from .enums import ExpenseCategory

class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = {'schema':'expenses_tracker', 'extend_existing': True}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('core.users.id', ondelete='CASCADE'), nullable=False)
    name = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    account = Column(Enum(ExpenseCategory), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="expenses")
    

