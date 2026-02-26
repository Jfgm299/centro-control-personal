# app/modules/expenses_tracker/__init__.py
from .expenses_router import router

TAGS = [
    {"name": "Expenses", "description": "Control de gastos personales"},
]

TAG_GROUP = {
    "name": "Expenses",
    "tags": ["Expenses"]
}

__all__ = ['router', 'TAGS', 'TAG_GROUP']