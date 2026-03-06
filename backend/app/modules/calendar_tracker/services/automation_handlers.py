"""
Handlers de automatizaciones de calendar_tracker.
Cada función sigue el contrato del motor:
    handler(payload, config, db, user_id) -> dict
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from ..models.reminder import Reminder
from ..enums import ReminderStatus


def handle_event_start(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: event_start
    payload: { event_id, start_at, category_id, enable_dnd }
    """
    cat_ids      = config.get("category_ids", [])
    dnd_only     = config.get("enable_dnd_only", False)
    category_id  = payload.get("category_id")
    enable_dnd   = payload.get("enable_dnd", False)

    if cat_ids and category_id not in cat_ids:
        return {"matched": False, "reason": "category_not_in_filter"}

    if dnd_only and not enable_dnd:
        return {"matched": False, "reason": "dnd_not_enabled_on_event"}

    return {"matched": True, "event_id": payload.get("event_id")}


def handle_event_end(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: event_end
    payload: { event_id, category_id }
    """
    cat_ids     = config.get("category_ids", [])
    category_id = payload.get("category_id")

    if cat_ids and category_id not in cat_ids:
        return {"matched": False, "reason": "category_not_in_filter"}

    return {"matched": True, "event_id": payload.get("event_id")}


def handle_reminder_due(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: reminder_due
    payload: { reminder_id, priority, due_date }
    """
    priority_order = {"low": 0, "medium": 1, "high": 2, "urgent": 3}
    min_priority   = config.get("min_priority", "high")
    payload_prio   = payload.get("priority", "medium")

    if priority_order.get(payload_prio, 0) < priority_order.get(min_priority, 2):
        return {"matched": False, "reason": "priority_below_threshold"}

    return {"matched": True, "reminder_id": payload.get("reminder_id")}


def action_create_event(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Acción: crear un evento en el calendario del usuario.
    """
    from datetime import timedelta
    from ..models.event import Event

    now   = datetime.now(timezone.utc)
    start = now
    end   = now + timedelta(minutes=config.get("duration_minutes", 30))

    event = Event(
        user_id=user_id,
        title=config.get("title", "Evento automático"),
        start_at=start,
        end_at=end,
        category_id=config.get("category_id"),
        enable_dnd=config.get("enable_dnd", False),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return {"created_event_id": event.id}


def action_push_summary_overdue(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Acción: enviar notificación con el resumen de recordatorios vencidos.
    Llamada típicamente por un cron de los domingos.
    """
    from ..models.notification import Notification

    today    = datetime.now(timezone.utc).date()
    overdue  = (
        db.query(Reminder)
        .filter(
            Reminder.user_id == user_id,
            Reminder.status  == ReminderStatus.PENDING,
            Reminder.due_date < today,
        )
        .count()
    )

    if overdue == 0:
        return {"sent": False, "reason": "no_overdue_reminders"}

    notification = Notification(
        user_id=user_id,
        trigger_at=datetime.now(timezone.utc),
        title="Recordatorios pendientes",
        body=f"Tienes {overdue} recordatorio{'s' if overdue > 1 else ''} vencido{'s' if overdue > 1 else ''}",
        status="pending",
    )
    db.add(notification)
    db.commit()
    return {"sent": True, "overdue_count": overdue}