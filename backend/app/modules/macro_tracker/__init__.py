from .macro_router import router
from .handlers import register_exception_handlers as register_handlers  # ← añadir

TAGS = [
    {"name": "Macros", "description": "Tracking de macronutrientes y calorías diarias"},
]
TAG_GROUP = {
    "name": "Macros",
    "tags": ["Macros"],
}

__all__ = ["router", "register_handlers", "TAGS", "TAG_GROUP"]