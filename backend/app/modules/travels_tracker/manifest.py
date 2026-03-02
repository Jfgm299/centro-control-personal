SCHEMA_NAME = "travels_tracker"

def get_settings():
    from app.core.config import settings
    return {
        "R2_ACCOUNT_ID":        getattr(settings, "R2_ACCOUNT_ID", ""),
        "R2_ACCESS_KEY_ID":     getattr(settings, "R2_ACCESS_KEY_ID", ""),
        "R2_SECRET_ACCESS_KEY": getattr(settings, "R2_SECRET_ACCESS_KEY", ""),
        "R2_BUCKET_NAME":       getattr(settings, "R2_BUCKET_NAME", ""),
        "R2_PUBLIC_URL":        getattr(settings, "R2_PUBLIC_URL", ""),
    }

USER_RELATIONSHIPS = [
    {
        "name": "trips",
        "target": "Trip",
        "back_populates": "user",
        "cascade": "all, delete-orphan",
    },
]