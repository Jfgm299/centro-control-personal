from .macro_router import router

TAGS = [
    {"name": "Macros", "description": "Tracking de macronutrientes y calorías diarias"},
]

TAG_GROUP = {
    "name": "Macros",
    "tags": ["Macros"],
}

__all__ = ["router", "TAGS", "TAG_GROUP"]