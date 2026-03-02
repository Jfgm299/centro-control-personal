SCHEMA_NAME = "flights_tracker"

def get_settings():
    from app.core.config import settings
    return {
        "AERODATABOX_API_KEY":  getattr(settings, "AERODATABOX_API_KEY", ""),
        "AERODATABOX_BASE_URL": getattr(settings, "AERODATABOX_BASE_URL", "https://aerodatabox.p.rapidapi.com"),
        "AERODATABOX_HOST":     getattr(settings, "AERODATABOX_HOST", "aerodatabox.p.rapidapi.com"),
    }

USER_RELATIONSHIPS = [
    {
        "name": "flights",
        "target": "Flight",
        "back_populates": "user",
        "cascade": "all, delete-orphan",
    },
]