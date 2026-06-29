"""
Application configuration loaded from environment variables / .env file.

All settings have sensible defaults so the service runs out of the box
without a .env file present.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Diagnostic Engine."""

    # -----------------------------------------------------------------
    # Service identity
    # -----------------------------------------------------------------
    SERVICE_NAME: str = "Diagnostic Engine"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_DESCRIPTION: str = (
        "Knowledge-based OBD-II Diagnostic Trouble Code lookup microservice."
    )

    # -----------------------------------------------------------------
    # Dataset
    # -----------------------------------------------------------------
    DATASET_PATH: str = "data/dtc_dataset.csv"

    # -----------------------------------------------------------------
    # Server
    # -----------------------------------------------------------------
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True

    # -----------------------------------------------------------------
    # Logging
    # -----------------------------------------------------------------
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Module-level singleton — import this everywhere.
settings = Settings()
