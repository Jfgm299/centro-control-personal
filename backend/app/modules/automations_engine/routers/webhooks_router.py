from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from ..schemas.webhook_schema import WebhookCreate, WebhookResponse, WebhookInboundPayload
from ..schemas.execution_schema import ExecutionResponse
from ..services import webhook_service, execution_service, automation_service, flow_executor
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.auth.user import User

router = APIRouter(tags=["Webhooks"])


@router.get("/automations/{automation_id}/webhooks", response_model=List[WebhookResponse])
def get_webhooks(
    automation_id: int,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    automation_service.get_by_id(automation_id, db, user_id=user.id)  # ← lanza 404 si no es suya
    return webhook_service.get_all(automation_id, db, user_id=user.id)


@router.post("/automations/{automation_id}/webhooks", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
def create_webhook(
    automation_id: int,
    data: WebhookCreate,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    return webhook_service.create(automation_id, db, data, user_id=user.id)


@router.delete("/automations/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_webhook(
    webhook_id: int,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    webhook_service.delete(webhook_id, db, user_id=user.id)


@router.post("/webhooks/in/{token}", status_code=status.HTTP_202_ACCEPTED)
def inbound_webhook(
    token:   str,
    payload: WebhookInboundPayload,
    db:      Session = Depends(get_db),
):
    webhook    = webhook_service.get_by_token(token, db)
    automation = automation_service.get_by_id(webhook.automation_id, db, user_id=webhook.user_id)
    
    # Fusiona source + data para que el flow tenga acceso a ambos
    trigger_payload = {"source": payload.source, **payload.data}
    
    execution  = execution_service.create(automation.id, webhook.user_id, trigger_payload, db)
    execution  = execution_service.mark_running(execution, db)

    try:
        result = flow_executor.execute(automation, trigger_payload, db, webhook.user_id)
    except Exception as e:
        execution = execution_service.mark_failed(execution, str(e), [], db)
        return {"execution_id": execution.id, "status": execution.status}

    if result["status"] == "success":
        execution = execution_service.mark_success(execution, result["node_logs"], db)
    else:
        execution = execution_service.mark_failed(execution, result.get("error", ""), result["node_logs"], db)

    return {"execution_id": execution.id, "status": execution.status}