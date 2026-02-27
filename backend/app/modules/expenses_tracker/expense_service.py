from sqlalchemy.orm import Session
from typing import List
from .expense import Expense
from .expense_schema import ExpenseCreate, ExpenseUpdate

class ExpenseService:

    def get_expenses(self, db: Session, user_id: int) -> List[Expense]:
        return db.query(Expense).filter(Expense.user_id == user_id).all()

    def get_expense(self, expense_id: int, db: Session, user_id: int) -> Expense:
        return db.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == user_id
        ).first()

    def create_expense(self, data: ExpenseCreate, db: Session, user_id: int) -> Expense:
        db_expense = Expense(**data.model_dump(), user_id=user_id)
        db.add(db_expense)
        db.commit()
        db.refresh(db_expense)
        return db_expense

    def update_expense(self, expense_id: int, data: ExpenseUpdate, db: Session, user_id: int) -> Expense:
        db_expense = db.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == user_id
        ).first()
        if not db_expense:
            return None
        update_data = data.model_dump(exclude_none=True)
        for key, value in update_data.items():
            setattr(db_expense, key, value)
        db.commit()
        db.refresh(db_expense)
        return db_expense

    def delete_expense(self, expense_id: int, db: Session, user_id: int) -> bool:
        db_expense = db.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == user_id
        ).first()
        if not db_expense:
            return False
        db.delete(db_expense)
        db.commit()
        return True