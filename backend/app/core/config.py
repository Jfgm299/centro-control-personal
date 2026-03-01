from pydantic_settings import BaseSettings
from pydantic import ConfigDict, field_validator
from pathlib import Path
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Modules
    INSTALLED_MODULES: List[str] = []

    @field_validator("INSTALLED_MODULES", mode="before")
    @classmethod
    def auto_discover_modules(cls, v):
        if v:
            return v
        from app.core.module_loader import get_installed_modules
        return get_installed_modules()

    # API
    API_VERSION: str = "v1"
    PROJECT_NAME: str = "Centro Control"
    DEBUG: bool = False

    # Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # AeroDataBox
    AERODATABOX_API_KEY: str
    AERODATABOX_BASE_URL: str = "https://aerodatabox.p.rapidapi.com"
    AERODATABOX_HOST: str = "aerodatabox.p.rapidapi.com"

    # OpenFoodFacts
    OFF_BASE_URL: str = "https://world.openfoodfacts.org"

    model_config = ConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",  # ← aquí
        case_sensitive=True,
    )


settings = Settings()