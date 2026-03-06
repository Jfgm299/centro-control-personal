import secrets
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from ..models.webhook_inbound import WebhookInbound
from ..schemas import WebhookCreate
from ..exceptions import WebhookNotFoundError, WebhookTokenInvalidError


class WebhookService:

    def get_all(self, automation_id: int, db: Session, user_id: int) -> List[WebhookInbound]:
        return db.query(WebhookInbound).filter(
            WebhookInbound.automation_id == automation_id,
            WebhookInbound.user_id       == user_id,
        ).all()

    def create(self, automation_id: int, db: Session, data: WebhookCreate, user_id: int) -> WebhookInbound:
        webhook = WebhookInbound(
            automation_id = automation_id,
            user_id       = user_id,
            token         = secrets.token_urlsafe(48),
            name          = data.name,
        )
        db.add(webhook)
        db.commit()
        db.refresh(webhook)
        return webhook

    def delete(self, webhook_id: int, db: Session, user_id: int) -> None:
        webhook = db.query(WebhookInbound).filter(
            WebhookInbound.id      == webhook_id,
            WebhookInbound.user_id == user_id,
        ).first()
        if not webhook:
            raise WebhookNotFoundError(webhook_id)
        db.delete(webhook)
        db.commit()

    def get_by_token(self, token: str, db: Session) -> WebhookInbound:
        webhook = db.query(WebhookInbound).filter(
            WebhookInbound.token     == token,
            WebhookInbound.is_active == True,
        ).first()
        if not webhook:
            raise WebhookTokenInvalidError()
        webhook.last_triggered_at = datetime.now(timezone.utc)
        db.commit()
        return webhook


webhook_service = WebhookService()