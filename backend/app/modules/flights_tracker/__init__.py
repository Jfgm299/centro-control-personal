from .flight_router import router

TAGS = [
    {"name": "Flights", "description": "Registro y tracking de vuelos"},
]

TAG_GROUP = {
    "name": "Flights",
    "tags": ["Flights"],
}

__all__ = ["router", "TAGS", "TAG_GROUP"]