from .calendar_router import router
from .handlers import register_exception_handlers as register_handlers

TAGS = [
    {"name": "Calendar", "description": "Gestion de eventos, recordatorios y rutinas"},
    {"name": "Reminders", "description": "Recordatorios pendientes de asignar"},
    {"name": "Routines", "description": "Rutinas recurrentes con patron override"},
    {"name": "Categories", "description": "Categorias personalizadas con color"},
]

TAG_GROUP = {
    "name": "Calendar",
    "tags": ["Calendar", "Reminders", "Routines", "Categories"],
}

__all__ = ["router", "register_handlers", "TAGS", "TAG_GROUP"]