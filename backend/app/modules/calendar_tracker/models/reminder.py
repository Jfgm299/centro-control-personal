from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core import Base
from ..enums import ReminderStatus, ReminderPriority


class Reminder(Base):
    __tablename__ = "reminders"
    __table_args__ = {"schema": "calendar_tracker", "extend_existing": True}

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("calendar_tracker.categories.id", ondelete="SET NULL"), nullable=True)
    title       = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status      = Column(
        SAEnum(ReminderStatus, schema="calendar_tracker", name="reminderstatus"),
        nullable=False,
        default=ReminderStatus.PENDING,
    )
    priority    = Column(
        SAEnum(ReminderPriority, schema="calendar_tracker", name="reminderpriority"),
        nullable=False,
        default=ReminderPriority.MEDIUM,
    )
    due_date    = Column(Date, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user     = relationship("User",     back_populates="reminders")
    category = relationship("Category", back_populates="reminders", foreign_keys=[category_id])
    event    = relationship("Event",    back_populates="reminder",  foreign_keys="Event.reminder_id", uselist=False)