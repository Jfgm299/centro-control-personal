from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core import Base


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = {"schema": "calendar_tracker", "extend_existing": True}

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id   = Column(Integer, ForeignKey("calendar_tracker.events.id", ondelete="CASCADE"), nullable=True)
    trigger_at = Column(DateTime(timezone=True), nullable=False, index=True)
    title      = Column(String(200), nullable=False)
    body       = Column(Text, nullable=False)
    sent_at    = Column(DateTime(timezone=True), nullable=True)
    status     = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user  = relationship("User",  back_populates="notifications")
    event = relationship("Event", back_populates="notifications", foreign_keys=[event_id])