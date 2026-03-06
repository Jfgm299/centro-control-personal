from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core import Base
from ..enums import ExecutionStatus


class Execution(Base):
    __tablename__ = "executions"
    __table_args__ = {"schema": "automations", "extend_existing": True}

    id              = Column(Integer, primary_key=True, index=True)
    automation_id   = Column(Integer, ForeignKey("automations.automations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id         = Column(Integer, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False, index=True)
    trigger_payload = Column(JSON, nullable=True)
    status          = Column(
        SAEnum(ExecutionStatus, schema="automations", name="executionstatus"),
        nullable=False,
        default=ExecutionStatus.PENDING,
    )
    started_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at   = Column(DateTime(timezone=True), nullable=True)
    duration_ms   = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    node_logs     = Column(JSON, nullable=True)

    user       = relationship("User",       back_populates="auto_executions")
    automation = relationship("Automation", back_populates="executions")