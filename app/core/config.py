"""
Application configuration using Pydantic Settings.
Loads environment variables with sensible defaults for local development.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration class for the Task Tracker application."""

    # Application metadata
    APP_NAME: str = "Task Tracker API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./task_tracker.db"

    # JWT Authentication
    SECRET_KEY: str = "change-this-secret-key-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REFRESH_TOKEN_COOKIE_NAME: str = "refresh_token"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"

    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
