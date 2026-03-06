from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core import Base


class ApiKey(Base):
    __tablename__ = "api_keys"
    __table_args__ = {"schema": "automations", "extend_existing": True}

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False, index=True)
    automation_id = Column(Integer, ForeignKey("automations.automations.id", ondelete="CASCADE"), nullable=True)
    name          = Column(String(100), nullable=False)
    key_hash      = Column(String(64), nullable=False, unique=True)
    key_prefix    = Column(String(8), nullable=False)
    scopes        = Column(JSON, nullable=False, default=list)
    last_used_at  = Column(DateTime(timezone=True), nullable=True)
    expires_at    = Column(DateTime(timezone=True), nullable=True)
    is_active     = Column(Boolean, nullable=False, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user       = relationship("User",       back_populates="api_keys")
    automation = relationship("Automation", back_populates="api_keys", foreign_keys=[automation_id])