from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from ..models.notification import Notification
from ..models.event import Event


class NotificationService:

    def schedule_for_event(self, db: Session, event: Event) -> Notification | None:
        """Crea una notificación pendiente para un evento con reminder_minutes."""
        if not event.reminder_minutes:
            return None

        trigger_at = event.start_at - timedelta(minutes=event.reminder_minutes)

        # No programar en el pasado
        if trigger_at <= datetime.now(timezone.utc):
            return None

        notification = Notification(
            user_id=event.user_id,
            event_id=event.id,
            trigger_at=trigger_at,
            title=event.title,
            body=f"Empieza en {event.reminder_minutes} min",
            status="pending",
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    def reschedule_for_event(self, db: Session, event: Event) -> None:
        """Cancela notificaciones pendientes previas y crea una nueva si aplica."""
        # Cancelar las pendientes existentes
        db.query(Notification).filter(
            Notification.event_id == event.id,
            Notification.status == "pending",
        ).delete(synchronize_session=False)
        db.commit()

        # Crear la nueva si tiene reminder_minutes
        if event.reminder_minutes:
            self.schedule_for_event(db, event)

    def get_pending_due(self, db: Session) -> list[Notification]:
        """Devuelve notificaciones pendientes cuyo trigger_at ya ha llegado."""
        now = datetime.now(timezone.utc)
        return (
            db.query(Notification)
            .filter(
                Notification.status == "pending",
                Notification.trigger_at <= now,
            )
            .all()
        )

    def mark_sent(self, db: Session, notification: Notification) -> None:
        notification.status = "sent"
        notification.sent_at = datetime.now(timezone.utc)
        db.commit()

    def mark_failed(self, db: Session, notification: Notification) -> None:
        notification.status = "failed"
        db.commit()