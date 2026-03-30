from datetime import date
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from .scheduled_expense_model import ScheduledExpense, ScheduledCategory, ScheduledFrequency
from .scheduled_expense_schema import ScheduledExpenseCreate, ScheduledExpenseUpdate
from .expense import Expense


class ScheduledExpenseService:

    def get_all(self, db: Session, user_id: int):
        items = (
            db.query(ScheduledExpense)
            .filter(
                ScheduledExpense.user_id == user_id,
                ScheduledExpense.is_active == True,
            )
            .order_by(ScheduledExpense.next_payment_date.asc().nullslast(),
                      ScheduledExpense.name.asc())
            .all()
        )
        self._auto_convert_past(items, db, user_id)
        return items

    def _auto_convert_past(self, items: list, db: Session, user_id: int):
        """
        Convierte automáticamente los gastos ONE_TIME y SUBSCRIPTION
        cuya fecha ya ha pasado en un gasto real (Expense).
        """
        today = date.today()
        changed = False
        # Acumular (item, expense) para despachar tras el commit
        converted_pairs: list = []

        for item in items:
            if not item.is_active or not item.next_payment_date:
                continue

            if item.next_payment_date <= today:
                if item.category == ScheduledCategory.ONE_TIME:
                    expense = Expense(
                        user_id=user_id,
                        name=item.name,
                        quantity=item.amount,
                        account=item.account,
                    )
                    db.add(expense)
                    item.is_active = False
                    changed = True
                    converted_pairs.append((item, expense))

                elif item.category == ScheduledCategory.SUBSCRIPTION:
                    while item.next_payment_date <= today:
                        expense = Expense(
                            user_id=user_id,
                            name=item.name,
                            quantity=item.amount,
                            account=item.account,
                        )
                        db.add(expense)
                        converted_pairs.append((item, expense))

                        if item.frequency == ScheduledFrequency.WEEKLY:
                            item.next_payment_date += relativedelta(weeks=1)
                        elif item.frequency == ScheduledFrequency.MONTHLY:
                            item.next_payment_date += relativedelta(months=1)
                        elif item.frequency == ScheduledFrequency.YEARLY:
                            item.next_payment_date += relativedelta(years=1)
                        elif item.frequency == ScheduledFrequency.CUSTOM and item.custom_days:
                            item.next_payment_date += relativedelta(days=item.custom_days)
                        else:
                            # Fallback just in case
                            item.next_payment_date += relativedelta(months=1)

                        changed = True

        if changed:
            db.commit()
            # Dispatch automation triggers after commit (IDs available now)
            for item, expense in converted_pairs:
                try:
                    db.refresh(expense)
                    from .automation_dispatcher import dispatcher
                    dispatcher.on_subscription_converted(
                        scheduled_id=item.id,
                        expense_id=expense.id,
                        name=item.name,
                        amount=item.amount,
                        user_id=user_id,
                        db=db,
                    )
                except Exception:
                    pass  # automation failures must never break the main flow

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
