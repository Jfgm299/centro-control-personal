from fastapi import APIRouter, Query, Depends, HTTPException
from ..enums import ExpenseCategory
from ..schemas import ExpenseCreate, ExpenseResponse, ExpenseUpdate
from ..models import Expense
from typing import List
from sqlalchemy.orm import Session
from ..services import ExpenseService

from ..database import get_db

router = APIRouter(prefix='/expenses', tags=['expenses'])
expense_service = ExpenseService()

@router.get('/',response_model=List[ExpenseResponse])
def get_expenses(
    db: Session = Depends(get_db)
): #Posibilidad de añadir parametros de control
    return expense_service.get_expenses(db)

@router.get('/{expense_id}', response_model=ExpenseResponse)
def get_expense(
    expense_id:int,
    db: Session = Depends(get_db)
):
    expense_db = expense_service.get_expense(expense_id,db)
    if not expense_db: raise HTTPException(status_code=404, detail='Expense not found')
    return expense_db

@router.post('/', response_model=ExpenseResponse, status_code=201)
def create_expense(
    data: ExpenseCreate,
    db: Session = Depends(get_db)
):
    return expense_service.create_expense(data,db)

@router.patch('/{expense_id}', response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    db: Session = Depends(get_db)
):
    expense_db = expense_service.update_expense(expense_id, data, db)
    if not expense_db: raise HTTPException(status_code=404, detail='Expense not found')
    return expense_db

@router.delete('/{expense_id}', response_description='Successfully deleted', status_code=204)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db)
):
    success = expense_service.delete_expense(expense_id, db)
    if not success: raise HTTPException(status_code=404, detail='Expense not found')
    return {"message": "Gasto eliminado", "id": expense_id}