from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core import Base


class Event(Base):
    __tablename__ = "events"
    __table_args__ = {"schema": "calendar_tracker", "extend_existing": True}

    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False, index=True)
    reminder_id      = Column(Integer, ForeignKey("calendar_tracker.reminders.id", ondelete="SET NULL"), nullable=True)
    routine_id       = Column(Integer, ForeignKey("calendar_tracker.routines.id",  ondelete="SET NULL"), nullable=True)
    category_id      = Column(Integer, ForeignKey("calendar_tracker.categories.id", ondelete="SET NULL"), nullable=True)
    title            = Column(String(200), nullable=False)
    description      = Column(Text, nullable=True)
    start_at         = Column(DateTime(timezone=True), nullable=False)
    end_at           = Column(DateTime(timezone=True), nullable=False)
    all_day          = Column(Boolean, nullable=False, default=False)
    color_override   = Column(String(7), nullable=True)
    enable_dnd       = Column(Boolean, nullable=False, default=False)
    reminder_minutes = Column(Integer, nullable=True)
    google_event_id  = Column(String(200), nullable=True)
    apple_event_id   = Column(String(200), nullable=True)
    is_cancelled     = Column(Boolean, nullable=False, default=False)
    created_at       = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at       = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    user          = relationship("User",         back_populates="events")
    category      = relationship("Category",     back_populates="events",    foreign_keys=[category_id])
    reminder      = relationship("Reminder",     back_populates="event",     foreign_keys=[reminder_id])
    routine       = relationship("Routine",      back_populates="events",    foreign_keys=[routine_id])
    notifications = relationship("Notification", back_populates="event",     cascade="all, delete-orphan")