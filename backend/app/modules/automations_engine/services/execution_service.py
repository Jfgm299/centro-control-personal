from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from ..models.execution import Execution
from ..enums import ExecutionStatus
from ..exceptions import ExecutionNotFoundError


class ExecutionService:

    def get_all(self, automation_id: int, db: Session, user_id: int) -> List[Execution]:
        return db.query(Execution).filter(
            Execution.automation_id == automation_id,
            Execution.user_id       == user_id,
        ).order_by(Execution.started_at.desc()).limit(100).all()

    def get_by_id(self, execution_id: int, db: Session, user_id: int) -> Execution:
        execution = db.query(Execution).filter(
            Execution.id      == execution_id,
            Execution.user_id == user_id,
        ).first()
        if not execution:
            raise ExecutionNotFoundError(execution_id)
        return execution

    def create(self, automation_id: int, user_id: int, trigger_payload: dict, db: Session) -> Execution:
        execution = Execution(
            automation_id   = automation_id,
            user_id         = user_id,
            trigger_payload = trigger_payload,
            status          = ExecutionStatus.PENDING,
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        return execution

    def mark_running(self, execution: Execution, db: Session) -> Execution:
        execution.status = ExecutionStatus.RUNNING
        db.commit()
        db.refresh(execution)
        return execution

    def mark_success(self, execution: Execution, node_logs: list, db: Session) -> Execution:
        now = datetime.now(timezone.utc)
        execution.status      = ExecutionStatus.SUCCESS
        execution.finished_at = now
        execution.duration_ms = int((now - execution.started_at).total_seconds() * 1000)
        execution.node_logs   = node_logs
        db.commit()
        db.refresh(execution)
        return execution

    def mark_failed(self, execution: Execution, error: str, node_logs: list, db: Session) -> Execution:
        now = datetime.now(timezone.utc)
        execution.status        = ExecutionStatus.FAILED
        execution.finished_at   = now
        execution.duration_ms   = int((now - execution.started_at).total_seconds() * 1000)
        execution.error_message = error
        execution.node_logs     = node_logs
        db.commit()
        db.refresh(execution)
        return execution


execution_service = ExecutionService()