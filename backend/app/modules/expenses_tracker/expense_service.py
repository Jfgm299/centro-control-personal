from sqlalchemy.orm import Session
from typing import List
from .expense import Expense
from .expense_schema import ExpenseCreate, ExpenseUpdate

class ExpenseService:
    def get_expenses(self,db: Session ) -> List[Expense]: #Posibilidad de añadir parametros de control
        query = db.query(Expense)
        #expenses = query.offset(skip).limit(limit).all() en caso que quieras añadir parametros
        return query.all() 
    
    def get_expense(self, expense_id: int, db: Session) -> Expense:
        db_expense = db.query(Expense).filter(Expense.id == expense_id).first()

        return db_expense
    
    def create_expense(self, data: ExpenseCreate, db: Session ) -> Expense:
        # Paso1: Convertir el shcema Pydantic a model SQLAlchemy
        db_expense = Expense(**data.model_dump())
        #data.model_dump() convierte ExpenseCreate a dict
        # ** desempaqueta: Expense(name= ..., quantity=...,etc)

        # Paso2: Añadir e objeto a la sesión (todavía no está en la DB)
        db.add(db_expense)

        # Paso3: guardar permanentemente en DB
        db.commit()

        #Paso4: Refrescar el objeto para obtener los campos generados
        db.refresh(db_expense)
        #Ahora db_expense.id y db_expense.created_at tienen valores

        return db_expense
    
    def update_expense(self, expense_id: int, data: ExpenseUpdate, db: Session) -> Expense:
        #Paso1: Buscar el gasto en la DB
        db_expense = db.query(Expense).filter(Expense.id == expense_id).first()

        #Paso2: 404 si no existe
        if not db_expense: return None
        #Paso3: actualizar solo los campos que vienen en el request
        #exclude_unset=True -> ignora los campos que el usuario no envió
        update_data = data.model_dump(exclude_none= True )

        for key, value in update_data.items():
            setattr(db_expense, key, value)

        #Paso4: guardar cambios
        db.commit()
        db.refresh(db_expense)

        return db_expense
    
    def delete_expense(self, expense_id: int, db: Session) -> bool:
        #Paso1: Buscar el gasto en la DB
        db_expense = db.query(Expense).filter(Expense.id == expense_id).first()

        #Paso2: 404 si no existe
        if not db_expense: return False

        #Paso3: eliminar

        db.delete(db_expense)
        db.commit()

        return True