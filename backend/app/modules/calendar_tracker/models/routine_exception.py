from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core import Base
from ..enums import RoutineExceptionAction


class RoutineException(Base):
    __tablename__ = "routine_exceptions"
    __table_args__ = {"schema": "calendar_tracker", "extend_existing": True}

    id            = Column(Integer, primary_key=True, index=True)
    routine_id    = Column(Integer, ForeignKey("calendar_tracker.routines.id", ondelete="CASCADE"), nullable=False, index=True)
    original_date = Column(Date, nullable=False)
    action        = Column(
        SAEnum(RoutineExceptionAction, schema="calendar_tracker", name="routineexceptionaction"),
        nullable=False,
    )
    new_start_at         = Column(DateTime(timezone=True), nullable=True)
    new_end_at           = Column(DateTime(timezone=True), nullable=True)
    new_title            = Column(String(200), nullable=True)
    new_enable_dnd       = Column(Boolean, nullable=True)
    new_reminder_minutes = Column(Integer, nullable=True)
    created_at           = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    routine = relationship("Routine", back_populates="exceptions")