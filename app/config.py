"""
Application Configuration

Centralized configuration management using Pydantic Settings.
Automatically loads from environment variables and .env file.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Why use Pydantic Settings?
    - Type validation: Ensures DATABASE_URL is a string, PORT is an int, etc.
    - Defaults: Provides sensible defaults for optional settings
    - Documentation: Clear list of all configuration options
    - .env support: Automatically loads from .env file

    All settings are loaded from environment variables or .env file.
    """

    # Database Configuration
    database_url: str
    database_echo: bool = True  # Log all SQL queries (useful for development)

    # API Configuration
    api_title: str = "Bank Statement Analyzer API"
    api_description: str = "API for analyzing bank statements using Claude AI"
    api_version: str = "1.0.0"

    # CORS Configuration (frontend URLs)
    cors_origins: list[str] = [
        "http://localhost:5173",  # Vite default
        "http://localhost:5174",
        "http://localhost:5175",
    ]

    # AI Configuration (for future use)
    anthropic_api_key: str | None = None

    # Logging Configuration
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Map environment variable names to settings
        env_prefix="",  # No prefix, use exact names
    )


@lru_cache
def get_settings() -> Settings:
    """
    Get application settings (cached).

    Uses @lru_cache to ensure settings are only loaded once.
    This is efficient and prevents repeated file reads.

    Usage:
        from app.config import get_settings
        settings = get_settings()
        print(settings.database_url)
    """
    return Settings()  # type: ignore[call-arg]
