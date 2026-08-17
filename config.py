from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

class Settings(BaseSettings):
    """
    Централизованные настройки приложения.
    Значения можно переопределить через переменные окружения или .env файл.
    """
    APP_NAME: str = "Medical Clinical Decision Support System — Rule-Based Expert Engine"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    KNOWLEDGE_DIR: str = Field(default="knowledge", alias="KNOWLEDGE_DIR")
    CONFIGS_DIR: str = Field(default="knowledge/configs", alias="CONFIGS_DIR")
    GUIDELINES_DIR: str = Field(default="knowledge/guidelines", alias="GUIDELINES_DIR")
    LABORATORY_DIR: str = Field(default="knowledge/laboratory", alias="LABORATORY_DIR")
    FONTS_DIR: str = Field(default="fonts", alias="FONTS_DIR")
    DATA_DIR: str = Field(default="data", alias="DATA_DIR")

    DB_PATH: str = Field(default="data/history.db", alias="DB_PATH")
    LOG_LEVEL: str = Field(default="INFO", alias="LOG_LEVEL")

    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", alias="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", alias="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    API_HOST: str = Field(default="0.0.0.0", alias="API_HOST")
    API_PORT: int = Field(default=8000, alias="API_PORT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()