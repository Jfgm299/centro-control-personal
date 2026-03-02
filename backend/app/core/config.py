from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from pathlib import Path
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # API
    API_VERSION: str = "v1"
    PROJECT_NAME: str = "Centro Control"
    DEBUG: bool = False

    # Módulos — auto-descubiertos, nunca se tocan
    INSTALLED_MODULES: List[str] = []

    model_config = ConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",
        case_sensitive=True,
        extra="allow",  # ← permite variables extra de módulos sin romper la validación
    )

    def __init__(self, **data):
        super().__init__(**data)
        if not self.INSTALLED_MODULES:
            from app.core.module_loader import get_installed_modules
            self.INSTALLED_MODULES = get_installed_modules()


settings = Settings()