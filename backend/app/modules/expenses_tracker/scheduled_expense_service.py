from datetime import date
from sqlalchemy.orm import Session
from .scheduled_expense_model import ScheduledExpense
from .scheduled_expense_schema import ScheduledExpenseCreate, ScheduledExpenseUpdate
from .expense import Expense


class ScheduledExpenseService:

    def get_all(self, db: Session, user_id: int):
        items = (
            db.query(ScheduledExpense)
            .filter(ScheduledExpense.user_id == user_id)
            .order_by(ScheduledExpense.next_payment_date.asc().nullslast(),
                      ScheduledExpense.name.asc())
            .all()
        )
        self._auto_convert_past(items, db, user_id)
        return items

    def _auto_convert_past(self, items: list, db: Session, user_id: int):
        """
        Convierte automáticamente los gastos ONE_TIME cuya fecha ya ha pasado
        en un gasto real (Expense) y los marca como inactivos.
        """
        today = date.today()
        changed = False

        for item in items:
            if (
                item.category == 'ONE_TIME'
                and item.is_active
                and item.next_payment_date
                and item.next_payment_date <= today
            ):
                # Crear gasto real
                expense = Expense(
                    user_id=user_id,
                    name=item.name,
                    quantity=item.amount,
                    account=item.account,
                )
                db.add(expense)

                # Marcar como inactivo para no volver a procesarlo
                item.is_active = False
                changed = True

        if changed:
            db.commit()

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