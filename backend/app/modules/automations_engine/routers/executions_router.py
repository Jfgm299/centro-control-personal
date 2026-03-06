from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..schemas.execution_schema import ExecutionResponse
from ..services import execution_service
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.auth.user import User
from ..services import automation_service

router = APIRouter(prefix="/automations", tags=["Executions"])


@router.get("/{automation_id}/executions", response_model=List[ExecutionResponse])
def get_executions(
    automation_id: int,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    automation_service.get_by_id(automation_id, db, user_id=user.id)  # ← lanza 404 si no es suya
    return execution_service.get_all(automation_id, db, user_id=user.id)


@router.get("/{automation_id}/executions/{execution_id}", response_model=ExecutionResponse)
def get_execution(
    automation_id: int,
    execution_id:  int,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    automation_service.get_by_id(automation_id, db, user_id=user.id)  # ← lanza 404 si no es suya
    return execution_service.get_by_id(execution_id, db, user_id=user.id)