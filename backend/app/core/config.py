import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # --- Database ---
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@db:5432/appdb"
    )
    
    # --- Authentication ---
    GOOGLE_CLIENT_ID: str = os.getenv(
        "GOOGLE_CLIENT_ID",
        "60209345033-dagb9pvr7maru9uq13i7ntoj4p513ls5.apps.googleusercontent.com"
    )
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-change-me")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_EXPIRE_MINUTES", 15))
    REFRESH_EXPIRE_DAYS: int = int(os.getenv("REFRESH_EXPIRE_DAYS", 15))
    
    # --- Application ---
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # --- Security ---
    SECURE_COOKIES: bool = os.getenv("SECURE_COOKIES", "False").lower() == "true"
    SAME_SITE_COOKIE: str = os.getenv("SAME_SITE_COOKIE", "lax")
    
    # --- Logging ---
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv(
        "LOG_FORMAT",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    logger.info(f"Loaded settings: DEBUG={settings.DEBUG}, LOG_LEVEL={settings.LOG_LEVEL}")
    return settings


settings = get_settings()