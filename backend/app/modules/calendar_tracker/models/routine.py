from sqlalchemy import Column, Integer, String, Text, Boolean, Date, Time, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core import Base


class Routine(Base):
    __tablename__ = "routines"
    __table_args__ = {"schema": "calendar_tracker", "extend_existing": True}

    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id      = Column(Integer, ForeignKey("calendar_tracker.categories.id", ondelete="SET NULL"), nullable=True)
    title            = Column(String(200), nullable=False)
    description      = Column(Text, nullable=True)
    rrule            = Column(Text, nullable=False)
    start_time       = Column(Time(timezone=False), nullable=False)
    end_time         = Column(Time(timezone=False), nullable=False)
    valid_from       = Column(Date, nullable=False)
    valid_until      = Column(Date, nullable=True)
    enable_dnd       = Column(Boolean, nullable=False, default=False)
    reminder_minutes = Column(Integer, nullable=True)
    is_active        = Column(Boolean, nullable=False, default=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user       = relationship("User",             back_populates="routines")
    category   = relationship("Category",         back_populates="routines",   foreign_keys=[category_id])
    exceptions = relationship("RoutineException", back_populates="routine",    cascade="all, delete-orphan")
    events     = relationship("Event",            back_populates="routine",    foreign_keys="Event.routine_id")