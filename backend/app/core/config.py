# app/core/config.py

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Modules - ← AQUÍ CONTROLAS QUÉ ESTÁ ACTIVO
    INSTALLED_MODULES: List[str] = [
        "expenses_tracker",
        "gym_tracker",
    ]

    # API
    API_VERSION: str = "v1"
    PROJECT_NAME: str = "Centro Control"
    DEBUG: bool = False

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


settings = Settings()