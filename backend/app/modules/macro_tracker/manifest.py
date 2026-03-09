SCHEMA_NAME = "macro_tracker"

# Variables de entorno propias del módulo.
# Se leen del mismo .env que el core. Si no existen, usan el default.
def get_settings():
    """Lazy import para evitar importar Settings antes de que esté lista."""
    import os
    from app.core.config import settings
    return {
        "OFF_BASE_URL": os.environ.get("OFF_BASE_URL") or getattr(settings, "OFF_BASE_URL", "https://world.openfoodfacts.org"),
    }


# Relaciones que este módulo añade al modelo User.
# module_loader.register_user_relationships() las registra automáticamente.
USER_RELATIONSHIPS = [
    {
        "name": "diary_entries",
        "target": "DiaryEntry",
        "back_populates": "user",
        "cascade": "all, delete-orphan",
        "uselist": True,
    },
    {
        "name": "user_goal",
        "target": "UserGoal",
        "back_populates": "user",
        "cascade": "all, delete-orphan",
        "uselist": False,
    },
]