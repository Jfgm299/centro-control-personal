# app/modules/expenses_tracker/__init__.py
from .expenses_router import router
#from .handlers.expenses_handlers import register_exception_handlers as register_handlers

TAGS = [{"name": "expenses", "description": "Gestión de gastos personales"}]
TAG_GROUP = {"name": "Expenses", "tags": ["Expenses"]}

__all__ = ["router", "register_handlers", "TAGS", "TAG_GROUP"]