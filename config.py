import os
import secrets
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "MedCDSS-RB"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    KNOWLEDGE_DIR: str = "knowledge"
    GUIDELINES_DIR: str = os.path.join(KNOWLEDGE_DIR, "guidelines")
    CONFIGS_DIR: str = os.path.join(KNOWLEDGE_DIR, "configs")
    FONTS_DIR: str = "fonts"
    LOG_LEVEL: str = "INFO"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    DB_PATH: str = "cdss.db"
    DATABASE_URL: str = "sqlite:///./cdss.db"

    REDIS_URL: Optional[str] = None

    # Генерируем секретный ключ, если он не задан через переменные окружения
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()