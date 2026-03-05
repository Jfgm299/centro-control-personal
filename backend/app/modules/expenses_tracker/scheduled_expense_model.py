from sqlalchemy import Column, Integer, Float, String, DateTime, Date, Boolean, Enum, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from .enums import ExpenseCategory
import enum


class ScheduledFrequency(str, enum.Enum):
    WEEKLY  = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY  = "YEARLY"
    CUSTOM  = "CUSTOM"


class ScheduledCategory(str, enum.Enum):
    SUBSCRIPTION = "SUBSCRIPTION"
    ONE_TIME     = "ONE_TIME"


class ScheduledExpense(Base):
    __tablename__ = "scheduled_expenses"
    __table_args__ = {'schema': 'expenses_tracker', 'extend_existing': True}

    id                = Column(Integer, primary_key=True)
    user_id           = Column(Integer, ForeignKey('core.users.id', ondelete='CASCADE'), nullable=False)
    name              = Column(String(100), nullable=False)
    amount            = Column(Float, nullable=False)
    account           = Column(Enum(ExpenseCategory), nullable=False)
    frequency         = Column(Enum(ScheduledFrequency, name='scheduledfrequency'), nullable=False, default=ScheduledFrequency.MONTHLY)
    category          = Column(Enum(ScheduledCategory, name='scheduledcategory'), nullable=False, default=ScheduledCategory.SUBSCRIPTION)
    next_payment_date = Column(Date, nullable=True)
    is_active         = Column(Boolean, nullable=False, default=True)
    icon              = Column(String(10), nullable=True)
    color             = Column(String(20), nullable=True)
    notes             = Column(Text, nullable=True)
    custom_days       = Column(Integer, nullable=True)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())
    updated_at        = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="scheduled_expenses")