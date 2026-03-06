from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core import Base
from ..enums import AutomationTriggerType


class Automation(Base):
    __tablename__ = "automations"
    __table_args__ = {"schema": "automations", "extend_existing": True}

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False, index=True)
    name         = Column(String(200), nullable=False)
    description  = Column(Text, nullable=True)
    is_active    = Column(Boolean, nullable=False, default=True)
    flow         = Column(JSON, nullable=False, default=lambda: {"nodes": [], "edges": []})
    trigger_type = Column(
        SAEnum(AutomationTriggerType, schema="automations", name="automationtriggertype"),
        nullable=False,
        default=AutomationTriggerType.MODULE_EVENT,
    )
    trigger_ref  = Column(String(200), nullable=True)
    run_count    = Column(Integer, nullable=False, default=0)
    last_run_at  = Column(DateTime(timezone=True), nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    user       = relationship("User",           back_populates="automations")
    executions = relationship("Execution",      back_populates="automation", cascade="all, delete-orphan")
    api_keys   = relationship("ApiKey",         back_populates="automation", cascade="all, delete-orphan")
    webhooks   = relationship("WebhookInbound", back_populates="automation", cascade="all, delete-orphan")