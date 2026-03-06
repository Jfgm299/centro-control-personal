from sqlalchemy.orm import Session
from typing import Optional
from ..models.reminder import Reminder
from ..enums import ReminderStatus, ReminderPriority
from ..calendar_schema import ReminderCreate, ReminderUpdate
from ..exceptions import ReminderNotFoundError, ReminderAlreadyScheduledError


class ReminderService:

    def get_all(
        self,
        db: Session,
        user_id: int,
        status: Optional[ReminderStatus] = None,
        priority: Optional[ReminderPriority] = None,
    ) -> list[Reminder]:
        q = db.query(Reminder).filter(Reminder.user_id == user_id)
        if status:
            q = q.filter(Reminder.status == status)
        if priority:
            q = q.filter(Reminder.priority == priority)
        return (
            q.order_by(Reminder.priority.desc(), Reminder.due_date.asc())
            .all()
        )

    def get_by_id(self, db: Session, user_id: int, reminder_id: int) -> Reminder:
        reminder = (
            db.query(Reminder)
            .filter(Reminder.id == reminder_id, Reminder.user_id == user_id)
            .first()
        )
        if not reminder:
            raise ReminderNotFoundError(reminder_id)
        return reminder

    def create(self, db: Session, user_id: int, data: ReminderCreate) -> Reminder:
        reminder = Reminder(
            user_id=user_id,
            title=data.title,
            description=data.description,
            category_id=data.category_id,
            priority=data.priority,
            due_date=data.due_date,
            status=ReminderStatus.PENDING,
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        return reminder

    def update(self, db: Session, user_id: int, reminder_id: int, data: ReminderUpdate) -> Reminder:
        reminder = self.get_by_id(db, user_id, reminder_id)
        update_data = data.model_dump(exclude_none=True)
        for key, value in update_data.items():
            setattr(reminder, key, value)
        db.commit()
        db.refresh(reminder)
        return reminder

    def delete(self, db: Session, user_id: int, reminder_id: int) -> None:
        reminder = self.get_by_id(db, user_id, reminder_id)
        db.delete(reminder)
        db.commit()

    def mark_scheduled(self, db: Session, reminder: Reminder) -> Reminder:
        """Llamado por event_service al crear el evento vinculado."""
        if reminder.status == ReminderStatus.SCHEDULED:
            raise ReminderAlreadyScheduledError(reminder.id)
        reminder.status = ReminderStatus.SCHEDULED
        db.commit()
        db.refresh(reminder)
        return reminder

    def mark_done(self, db: Session, reminder: Reminder) -> Reminder:
        reminder.status = ReminderStatus.DONE
        db.commit()
        db.refresh(reminder)
        return reminder

    def mark_pending(self, db: Session, reminder: Reminder) -> Reminder:
        """Llamado por event_service al eliminar el evento vinculado."""
        reminder.status = ReminderStatus.PENDING
        db.commit()
        db.refresh(reminder)
        return reminder