"""Database engine and session factory.

Production uses PostgreSQL (psycopg). SQLite is fully supported for local
development and the test-suite via the ``DATABASE_URL`` setting, so the
application and every test run without external infrastructure.
"""

import logging

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def build_engine(url: str | None = None) -> Engine:
    """Create the SQLAlchemy engine for the configured database URL.

    SQLite in-memory databases use a static pool so the same underlying
    connection is shared across sessions (required for ``:memory:``).
    """
    settings = get_settings()
    database_url = url or settings.database_url
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        if ":memory:" in database_url:
            return create_engine(
                database_url,
                connect_args=connect_args,
                poolclass=StaticPool,
            )
    try:
        return create_engine(database_url, pool_pre_ping=True)
    except (ImportError, Exception) as exc:
        logger.warning(
            "Could not load driver for %s (%s); falling back to local SQLite engine",
            database_url,
            exc,
        )
        return create_engine("sqlite:///idealens.db", connect_args={"check_same_thread": False})


engine = build_engine()

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session():
    """FastAPI dependency that yields a database session per request."""
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_schema(url: str | None = None) -> None:
    """Create all tables for the given database URL (development/CI helper).

    Production schema changes should be applied through reviewed migrations;
    this helper exists so local development and tests can bootstrap quickly.
    """
    from app.models import Base  # noqa: PLC0415 - avoid circular import at module load

    target_engine = engine if url is None else build_engine(url)
    Base.metadata.create_all(bind=target_engine)
    logger.info("Database schema created (URL scheme: %s)", url or get_settings().database_url)
