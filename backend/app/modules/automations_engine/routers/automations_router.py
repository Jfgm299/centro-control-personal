from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from ..schemas import AutomationCreate, AutomationUpdate, AutomationFlowUpdate, AutomationResponse
from ..schemas.execution_schema import ExecutionTriggerRequest, ExecutionResponse
from ..services import automation_service, execution_service, flow_executor
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.auth.user import User

router = APIRouter(prefix="/automations", tags=["Automations"])


@router.get("/", response_model=List[AutomationResponse])
def get_automations(
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    return automation_service.get_all(db, user_id=user.id)


@router.post("/", response_model=AutomationResponse, status_code=status.HTTP_201_CREATED)
def create_automation(
    data: AutomationCreate,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    return automation_service.create(db, data, user_id=user.id)


@router.get("/{automation_id}", response_model=AutomationResponse)
def get_automation(
    automation_id: int,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    return automation_service.get_by_id(automation_id, db, user_id=user.id)


@router.patch("/{automation_id}", response_model=AutomationResponse)
def update_automation(
    automation_id: int,
    data: AutomationUpdate,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    return automation_service.update(automation_id, db, data, user_id=user.id)


@router.put("/{automation_id}/flow", response_model=AutomationResponse)
def update_automation_flow(
    automation_id: int,
    data: AutomationFlowUpdate,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    return automation_service.update_flow(automation_id, db, data, user_id=user.id)


@router.delete("/{automation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_automation(
    automation_id: int,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    automation_service.delete(automation_id, db, user_id=user.id)


@router.post("/{automation_id}/trigger", response_model=ExecutionResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_automation(
    automation_id: int,
    data: ExecutionTriggerRequest,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    automation = automation_service.get_by_id(automation_id, db, user_id=user.id)
    execution  = execution_service.create(automation_id, user.id, data.payload, db)
    execution  = execution_service.mark_running(execution, db)

    result = flow_executor.execute(automation, data.payload, db, user.id)

    if result["status"] == "success":
        execution = execution_service.mark_success(execution, result["node_logs"], db)
    else:
        execution = execution_service.mark_failed(execution, result.get("error", ""), result["node_logs"], db)

    return execution