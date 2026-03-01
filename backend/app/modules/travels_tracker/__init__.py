from .routers import router
from .handlers import register_exception_handlers as register_handlers

TAGS = [
    {"name": "Travels", "description": "Registro y tracking de viajes"},
]
TAG_GROUP = {
    "name": "Travels",
    "tags": ["Travels"],
}

__all__ = ["router", "register_handlers", "TAGS", "TAG_GROUP"]