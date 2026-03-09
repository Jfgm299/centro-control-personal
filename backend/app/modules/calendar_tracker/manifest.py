SCHEMA_NAME = "calendar_tracker"


def get_settings():
    """Lazy import para evitar importar Settings antes de que esté lista."""
    import os
    from app.core.config import settings
    return {
        "FIREBASE_CREDENTIALS_JSON": os.environ.get("FIREBASE_CREDENTIALS_JSON") or getattr(settings, "FIREBASE_CREDENTIALS_JSON", ""),
        "GOOGLE_CLIENT_ID":          os.environ.get("GOOGLE_CLIENT_ID")          or getattr(settings, "GOOGLE_CLIENT_ID", ""),
        "GOOGLE_CLIENT_SECRET":      os.environ.get("GOOGLE_CLIENT_SECRET")      or getattr(settings, "GOOGLE_CLIENT_SECRET", ""),
        "GOOGLE_REDIRECT_URI":       os.environ.get("GOOGLE_REDIRECT_URI")       or getattr(settings, "GOOGLE_REDIRECT_URI", ""),
        "ENCRYPTION_KEY":            os.environ.get("ENCRYPTION_KEY")            or getattr(settings, "ENCRYPTION_KEY", ""),
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
    {
        "name": "calendar_connections",
        "target": "CalendarConnection",
        "back_populates": "user",
        "cascade": "all, delete-orphan",
        "uselist": True,
    },
    {
        "name": "sync_logs",
        "target": "SyncLog",
        "back_populates": "user",
        "cascade": "all, delete-orphan",
        "uselist": True,
    },
]