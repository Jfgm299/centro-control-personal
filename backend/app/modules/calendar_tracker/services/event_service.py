from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from ..models.event import Event
from ..models.reminder import Reminder
from ..enums import ReminderStatus
from ..schemas.calendar_schema import EventCreate, EventUpdate, ReminderSchedule
from ..exceptions import (
    EventNotFoundError,
    ReminderNotFoundError,
    ReminderAlreadyScheduledError,
    InvalidEventRangeError,
)
from .notification_service import NotificationService

notification_service = NotificationService()


def _load_event(db: Session, event_id: int, user_id: int) -> Event:
    event = (
        db.query(Event)
        .options(joinedload(Event.category))
        .filter(Event.id == event_id, Event.user_id == user_id, Event.is_cancelled == False)
        .first()
    )
    if not event:
        raise EventNotFoundError(event_id)
    return event


class EventService:

    def get_range(
        self,
        db: Session,
        user_id: int,
        start: datetime,
        end: datetime,
    ) -> list[Event]:
        if end <= start:
            raise InvalidEventRangeError()
        return (
            db.query(Event)
            .options(joinedload(Event.category))
            .filter(
                Event.user_id == user_id,
                Event.is_cancelled == False,
                Event.start_at >= start,
                Event.start_at < end,
            )
            .order_by(Event.start_at)
            .all()
        )

    def get_today(self, db: Session, user_id: int) -> list[Event]:
        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end   = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        return (
            db.query(Event)
            .options(joinedload(Event.category))
            .filter(
                Event.user_id == user_id,
                Event.is_cancelled == False,
                Event.start_at >= start,
                Event.start_at <= end,
            )
            .order_by(Event.start_at)
            .all()
        )

    def get_by_id(self, db: Session, user_id: int, event_id: int) -> Event:
        return _load_event(db, event_id, user_id)

    def create(self, db: Session, user_id: int, data: EventCreate) -> Event:
        event = Event(
            user_id=user_id,
            title=data.title,
            description=data.description,
            category_id=data.category_id,
            start_at=data.start_at,
            end_at=data.end_at,
            all_day=data.all_day,
            color_override=data.color_override,
            enable_dnd=data.enable_dnd,
            reminder_minutes=data.reminder_minutes,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        # Programar notificación si tiene reminder_minutes
        if event.reminder_minutes:
            notification_service.schedule_for_event(db, event)
        return _load_event(db, event.id, user_id)

    def create_from_reminder(
        self,
        db: Session,
        user_id: int,
        reminder_id: int,
        data: ReminderSchedule,
    ) -> Event:
        reminder = (
            db.query(Reminder)
            .filter(Reminder.id == reminder_id, Reminder.user_id == user_id)
            .first()
        )
        if not reminder:
            raise ReminderNotFoundError(reminder_id)
        if reminder.status == ReminderStatus.SCHEDULED:
            raise ReminderAlreadyScheduledError(reminder_id)

        event = Event(
            user_id=user_id,
            reminder_id=reminder_id,
            category_id=reminder.category_id,
            title=reminder.title,
            description=reminder.description,
            start_at=data.start_at,
            end_at=data.end_at,
            color_override=data.color_override,
            enable_dnd=data.enable_dnd,
            reminder_minutes=data.reminder_minutes,
        )
        db.add(event)

        reminder.status = ReminderStatus.SCHEDULED
        db.commit()
        db.refresh(event)

        if event.reminder_minutes:
            notification_service.schedule_for_event(db, event)

        return _load_event(db, event.id, user_id)


    def update(self, db: Session, user_id: int, event_id: int, data: EventUpdate) -> Event:
        event = _load_event(db, event_id, user_id)

        update_data = data.model_dump(exclude_none=True)

        # Validar rango usando los valores resultantes (mezcla de nuevos y existentes)
        new_start = update_data.get("start_at", event.start_at)
        new_end   = update_data.get("end_at",   event.end_at)
        if new_end <= new_start:
            from ..exceptions import InvalidEventRangeError
            raise InvalidEventRangeError()

        for key, value in update_data.items():
            setattr(event, key, value)

        db.commit()
        db.refresh(event)

        if "start_at" in update_data or "reminder_minutes" in update_data:
            notification_service.reschedule_for_event(db, event)

        return _load_event(db, event_id, user_id)

    # services/event_service.py — método complete()

    def complete(self, db: Session, user_id: int, event_id: int) -> Event:
        event = _load_event(db, event_id, user_id)

        if event.reminder_id:
            reminder = db.query(Reminder).filter(Reminder.id == event.reminder_id).first()
            if reminder:
                reminder.status = ReminderStatus.DONE

        event.is_cancelled = True
        db.commit()
        db.refresh(event)
        return event  # ← devolver directamente, no llamar a _load_event

    def delete(self, db: Session, user_id: int, event_id: int) -> None:
        event = _load_event(db, event_id, user_id)

        # Si venía de un reminder, devolverlo a pending
        if event.reminder_id:
            reminder = db.query(Reminder).filter(Reminder.id == event.reminder_id).first()
            if reminder:
                reminder.status = ReminderStatus.PENDING

        db.delete(event)
        db.commit()