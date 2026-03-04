from sqlalchemy.orm import Session
from .scheduled_expense_model import ScheduledExpense
from .scheduled_expense_schema import ScheduledExpenseCreate, ScheduledExpenseUpdate


class ScheduledExpenseService:

    def get_all(self, db: Session, user_id: int):
        return (
            db.query(ScheduledExpense)
            .filter(ScheduledExpense.user_id == user_id)
            .order_by(ScheduledExpense.next_payment_date.asc().nullslast(),
                      ScheduledExpense.name.asc())
            .all()
        )

    def get_one(self, id: int, db: Session, user_id: int):
        return (
            db.query(ScheduledExpense)
            .filter(ScheduledExpense.id == id, ScheduledExpense.user_id == user_id)
            .first()
        )

    def create(self, data: ScheduledExpenseCreate, db: Session, user_id: int):
        obj = ScheduledExpense(**data.model_dump(), user_id=user_id)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, id: int, data: ScheduledExpenseUpdate, db: Session, user_id: int):
        obj = self.get_one(id, db, user_id)
        if not obj:
            return None
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(obj, field, value)
        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, id: int, db: Session, user_id: int):
        obj = self.get_one(id, db, user_id)
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True