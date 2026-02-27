from fastapi import APIRouter, Depends, HTTPException
from .expense_schema import ExpenseCreate, ExpenseResponse, ExpenseUpdate
from typing import List
from sqlalchemy.orm import Session
from .expense_service import ExpenseService
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.auth.user import User

router = APIRouter(prefix='/expenses', tags=['Expenses'])
expense_service = ExpenseService()

@router.get('/', response_model=List[ExpenseResponse])
def get_expenses(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return expense_service.get_expenses(db, user_id=user.id)

@router.get('/{expense_id}', response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    expense_db = expense_service.get_expense(expense_id, db, user_id=user.id)
    if not expense_db:
        raise HTTPException(status_code=404, detail='Expense not found')
    return expense_db

@router.post('/', response_model=ExpenseResponse, status_code=201)
def create_expense(
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return expense_service.create_expense(data, db, user_id=user.id)

@router.patch('/{expense_id}', response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    expense_db = expense_service.update_expense(expense_id, data, db, user_id=user.id)
    if not expense_db:
        raise HTTPException(status_code=404, detail='Expense not found')
    return expense_db

@router.delete('/{expense_id}', response_description='Successfully deleted', status_code=204)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    success = expense_service.delete_expense(expense_id, db, user_id=user.id)
    if not success:
        raise HTTPException(status_code=404, detail='Expense not found')
    return {"message": "Gasto eliminado", "id": expense_id}