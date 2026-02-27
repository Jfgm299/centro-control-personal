from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Modules
    INSTALLED_MODULES: List[str] = [
        "expenses_tracker",
        "gym_tracker",
    ]

    # API
    API_VERSION: str = "v1"
    PROJECT_NAME: str = "Centro Control"
    DEBUG: bool = False

    # Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15    # ← bajado a 15 minutos
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30      # ← nuevo

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


settings = Settings()