from .flight_router import router
from .handlers import register_exception_handlers as register_handlers  # ← añadir

TAGS = [
    {"name": "Flights", "description": "Registro y tracking de vuelos"},
]
TAG_GROUP = {
    "name": "Flights",
    "tags": ["Flights"],
}

__all__ = ["router", "register_handlers", "TAGS", "TAG_GROUP"]