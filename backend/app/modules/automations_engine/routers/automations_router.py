import json
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
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

    try:
        result = flow_executor.execute(automation, data.payload, db, user.id)
    except Exception as e:
        execution = execution_service.mark_failed(execution, str(e), [], db)
        return execution

    if result["status"] == "success":
        execution = execution_service.mark_success(execution, result["node_logs"], db)
    else:
        execution = execution_service.mark_failed(execution, result.get("error", ""), result["node_logs"], db)

    return execution


@router.post("/{automation_id}/trigger/stream")
def trigger_automation_stream(
    automation_id: int,
    data: ExecutionTriggerRequest,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """
    Ejecuta la automatización y hace streaming SSE de cada nodo en tiempo real.
    Emite: node_start → node → node_start → node → ... → done
    El evento "done" incluye node_logs completos para guardar la ejecución en el historial.
    """
    automation = automation_service.get_by_id(automation_id, db, user_id=user.id)
    execution  = execution_service.create(automation_id, user.id, data.payload, db)
    execution  = execution_service.mark_running(execution, db)

    # Capturar IDs antes de que la sesión se cierre al retornar el endpoint
    automation_id_val = automation.id
    execution_id_val  = execution.id
    user_id_val       = user.id
    payload_val       = data.payload

    def generate():
        from app.core.database import SessionLocal
        stream_db = SessionLocal()
        try:
            from ..models.automation import Automation
            from ..models.execution import Execution
            stream_automation = stream_db.get(Automation, automation_id_val)
            stream_execution  = stream_db.get(Execution, execution_id_val)
            final_event       = None

            for event in flow_executor.execute_stream(stream_automation, payload_val, stream_db, user_id_val):
                yield f"data: {json.dumps(event)}\n\n"
                if event["type"] == "done":
                    final_event = event

            if final_event:
                if final_event["status"] == "success":
                    execution_service.mark_success(stream_execution, final_event["node_logs"], stream_db)
                else:
                    execution_service.mark_failed(
                        stream_execution,
                        final_event.get("error_message", ""),
                        final_event["node_logs"],
                        stream_db,
                    )
        finally:
            stream_db.close()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering": "no",   # evita que nginx bufferice la respuesta
        },
    )