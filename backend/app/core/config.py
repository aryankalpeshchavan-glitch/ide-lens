"""Application configuration via environment variables (pydantic-settings).

Secrets (API keys, tokens) are read exclusively from environment variables or a
``git-ignored`` `.env` file — never hard-coded, never committed.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven settings for the IdeaLens backend.

    Values come from a `.env` file (see ``.env.example``) or from process
    environment variables, using ``UPPER_SNAKE_CASE`` names. The application
    boots with the defaults below; PostgreSQL and Redis are not required for
    the process itself to run.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"

    app_name: str = "IdeaLens API"

    database_url: str = "postgresql+psycopg://idealens:idealens@localhost:5432/idealens"

    redis_url: str = "redis://localhost:6379/0"

    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    dependency_check_timeout_seconds: float = 2.0

    # --- Research pipeline ---------------------------------------------------
    enabled_adapters: str = "semantic_scholar,crossref,arxiv,github"
    retrieval_limit_per_source: int = 10
    retrieval_max_concurrency: int = 4
    http_timeout_seconds: float = 30.0
    http_max_retries: int = 3
    excerpt_char_limit: int = 500

    # --- Queue / workers -----------------------------------------------------
    queue_key: str = "idealens:research:queue"
    queue_block_seconds: int = 5
    run_sync_execution: bool = False

    # --- AI / embedding providers (optional; secrets via env only) -----------
    ai_provider: str = "none"
    embedding_provider: str = "none"
    ai_api_key: str = ""
    embedding_api_key: str = ""
    github_token: str = ""
    semantic_scholar_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    """Return the application settings (cached for the process lifetime)."""
    return Settings()
