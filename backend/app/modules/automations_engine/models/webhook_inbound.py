from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core import Base


class WebhookInbound(Base):
    __tablename__ = "webhooks_inbound"
    __table_args__ = {"schema": "automations", "extend_existing": True}

    id                = Column(Integer, primary_key=True, index=True)
    automation_id     = Column(Integer, ForeignKey("automations.automations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id           = Column(Integer, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False, index=True)
    token             = Column(String(64), nullable=False, unique=True)
    name              = Column(String(100), nullable=False)
    is_active         = Column(Boolean, nullable=False, default=True)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    created_at        = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user       = relationship("User",       back_populates="inbound_webhooks")
    automation = relationship("Automation", back_populates="webhooks", foreign_keys=[automation_id])