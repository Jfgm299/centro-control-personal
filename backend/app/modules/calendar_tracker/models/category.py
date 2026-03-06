from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = {"schema": "calendar_tracker", "extend_existing": True}

    id                       = Column(Integer, primary_key=True, index=True)
    user_id                  = Column(Integer, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False, index=True)
    name                     = Column(String(100), nullable=False)
    color                    = Column(String(7), nullable=False)
    icon                     = Column(String(50), nullable=True)
    default_enable_dnd       = Column(Boolean, nullable=False, default=False)
    default_reminder_minutes = Column(Integer, nullable=True)
    created_at               = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user      = relationship("User",     back_populates="calendar_categories")
    events    = relationship("Event",    back_populates="category", foreign_keys="Event.category_id")
    reminders = relationship("Reminder", back_populates="category", foreign_keys="Reminder.category_id")
    routines  = relationship("Routine",  back_populates="category", foreign_keys="Routine.category_id")