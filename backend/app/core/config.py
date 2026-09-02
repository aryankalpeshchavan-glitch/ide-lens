"""Application configuration via environment variables (pydantic-settings)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven settings for the IdeaLens backend.

    Values come from a ``.env`` file (see ``.env.example``) or from process
    environment variables, using ``UPPER_SNAKE_CASE`` names. The application
    boots with the defaults below; PostgreSQL and Redis are not required for
    the process itself to run.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    #: Runtime environment: development | test | production
    environment: str = "development"

    #: Human-readable application name used in the /health response.
    app_name: str = "IdeaLens API"

    #: SQLAlchemy PostgreSQL connection string (psycopg driver).
    database_url: str = "postgresql+psycopg://idealens:idealens@localhost:5432/idealens"

    #: Redis connection string (queues/cache; not used by the M1 process).
    redis_url: str = "redis://localhost:6379/0"

    #: Allowed CORS origins for the Next.js frontend (JSON list).
    cors_origins: list[str] = ["http://localhost:3000"]

    #: Max seconds for the /health dependency probes.
    dependency_check_timeout_seconds: float = 2.0


@lru_cache
def get_settings() -> Settings:
    """Return the application settings (cached for the process lifetime)."""
    return Settings()