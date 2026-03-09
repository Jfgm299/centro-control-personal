SCHEMA_NAME = "travels_tracker"

def get_settings():
    import os
    from app.core.config import settings
    return {
        "R2_ACCOUNT_ID":        os.environ.get("R2_ACCOUNT_ID")        or getattr(settings, "R2_ACCOUNT_ID", ""),
        "R2_ACCESS_KEY_ID":     os.environ.get("R2_ACCESS_KEY_ID")     or getattr(settings, "R2_ACCESS_KEY_ID", ""),
        "R2_SECRET_ACCESS_KEY": os.environ.get("R2_SECRET_ACCESS_KEY") or getattr(settings, "R2_SECRET_ACCESS_KEY", ""),
        "R2_BUCKET_NAME":       os.environ.get("R2_BUCKET_NAME")       or getattr(settings, "R2_BUCKET_NAME", ""),
        "R2_PUBLIC_URL":        os.environ.get("R2_PUBLIC_URL")        or getattr(settings, "R2_PUBLIC_URL", ""),
    }

USER_RELATIONSHIPS = [
    {
        "name": "trips",
        "target": "Trip",
        "back_populates": "user",
        "cascade": "all, delete-orphan",
    },
]