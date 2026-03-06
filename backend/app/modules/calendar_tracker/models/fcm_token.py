from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core import Base


class FcmToken(Base):
    __tablename__ = "fcm_tokens"
    __table_args__ = {"schema": "calendar_tracker", "extend_existing": True}

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False, index=True)
    token        = Column(Text, nullable=False, unique=True)
    device_type  = Column(String(20), nullable=False)
    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="fcm_tokens")