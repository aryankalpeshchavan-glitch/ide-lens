"""Database infrastructure boundary.

M1 scope: configuration and session infrastructure only.

- No domain entities and no tables are created yet (DATA_MODEL.md entities
  arrive in a later milestone together with migrations).
- Creating the engine does **not** open a connection, so the application boots
  even when PostgreSQL is not running.
- No database schema is created at application startup.
"""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Declarative base class for future domain models (added in M2+)."""


def make_engine() -> Engine:
    """Build the SQLAlchemy engine from the configured ``DATABASE_URL``.

    The engine connects lazily: PostgreSQL is only required when a connection
    is actually opened (for example by the /health probe or by later
    milestones), not when the application starts.
    """
    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": settings.dependency_check_timeout_seconds},
    )


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)