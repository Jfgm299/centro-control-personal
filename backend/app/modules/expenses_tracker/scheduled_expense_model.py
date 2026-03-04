from sqlalchemy import Column, Integer, Float, String, DateTime, Date, Boolean, Enum, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from .enums import ExpenseCategory
import enum


class ScheduledFrequency(str, enum.Enum):
    WEEKLY   = "weekly"
    MONTHLY  = "monthly"
    YEARLY   = "yearly"
    CUSTOM   = "custom"


class ScheduledCategory(str, enum.Enum):
    SUBSCRIPTION = "subscription"
    RECURRING    = "recurring"
    INSTALLMENT  = "installment"


class ScheduledExpense(Base):
    __tablename__ = "scheduled_expenses"
    __table_args__ = {'schema': 'expenses_tracker', 'extend_existing': True}

    id              = Column(Integer, primary_key=True)
    user_id         = Column(Integer, ForeignKey('core.users.id', ondelete='CASCADE'), nullable=False)
    name            = Column(String(100), nullable=False)
    amount          = Column(Float, nullable=False)
    account         = Column(Enum(ExpenseCategory), nullable=False)
    frequency       = Column(Enum(ScheduledFrequency), nullable=False, default=ScheduledFrequency.MONTHLY)
    category        = Column(Enum(ScheduledCategory), nullable=False, default=ScheduledCategory.SUBSCRIPTION)
    next_payment_date = Column(Date, nullable=True)
    is_active       = Column(Boolean, nullable=False, default=True)
    icon            = Column(String(10), nullable=True)   # emoji
    color           = Column(String(20), nullable=True)   # hex color
    notes           = Column(Text, nullable=True)
    custom_days     = Column(Integer, nullable=True)      # solo si frequency=CUSTOM
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="scheduled_expenses")