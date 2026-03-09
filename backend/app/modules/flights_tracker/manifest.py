SCHEMA_NAME = "flights_tracker"

def get_settings():
    import os
    from app.core.config import settings
    return {
        "AERODATABOX_API_KEY":  os.environ.get("AERODATABOX_API_KEY") or getattr(settings, "AERODATABOX_API_KEY", ""),
        "AERODATABOX_BASE_URL": os.environ.get("AERODATABOX_BASE_URL") or getattr(settings, "AERODATABOX_BASE_URL", "https://aerodatabox.p.rapidapi.com"),
        "AERODATABOX_HOST":     os.environ.get("AERODATABOX_HOST")     or getattr(settings, "AERODATABOX_HOST", "aerodatabox.p.rapidapi.com"),
    }

USER_RELATIONSHIPS = [
    {
        "name": "flights",
        "target": "Flight",
        "back_populates": "user",
        "cascade": "all, delete-orphan",
    },
]