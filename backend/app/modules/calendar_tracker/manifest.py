SCHEMA_NAME = "calendar_tracker"


def get_settings():
    """Lazy import para evitar importar Settings antes de que esté lista."""
    from app.core.config import settings
    return {
        "FIREBASE_CREDENTIALS_JSON": getattr(settings, "FIREBASE_CREDENTIALS_JSON", ""),
        "GOOGLE_CLIENT_ID":          getattr(settings, "GOOGLE_CLIENT_ID", ""),
        "GOOGLE_CLIENT_SECRET":      getattr(settings, "GOOGLE_CLIENT_SECRET", ""),
        "GOOGLE_REDIRECT_URI":       getattr(settings, "GOOGLE_REDIRECT_URI", ""),
        "ENCRYPTION_KEY":            getattr(settings, "ENCRYPTION_KEY", ""),
    }


USER_RELATIONSHIPS = [
    {
        "name": "events",
        "target": "Event",
        "back_populates": "user",
        "cascade": "all, delete-orphan",
        "uselist": True,
    },
    {
        "name": "reminders",
        "target": "Reminder",
        "back_populates": "user",
        "cascade": "all, delete-orphan",
        "uselist": True,
    },
    {
        "name": "routines",
        "target": "Routine",
        "back_populates": "user",
        "cascade": "all, delete-orphan",
        "uselist": True,
    },
    {
        "name": "calendar_categories",
        "target": "Category",
        "back_populates": "user",
        "cascade": "all, delete-orphan",
        "uselist": True,
    },
    {
        "name": "notifications",
        "target": "Notification",
        "back_populates": "user",
        "cascade": "all, delete-orphan",
        "uselist": True,
    },
    {
        "name": "fcm_tokens",
        "target": "FcmToken",
        "back_populates": "user",
        "cascade": "all, delete-orphan",
        "uselist": True,
    },
]