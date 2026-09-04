"""Pytest configuration: SQLite in-memory database and sync execution for tests.

Environment variables MUST be set before any application code is imported so
that the module-level ``engine`` and ``SessionLocal`` use SQLite. ``lru_cache``
on ``get_settings`` then caches the test configuration for the process life.
"""

import os

# Set test-safe defaults *before* importing any app code.
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("RUN_SYNC_EXECUTION", "true")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")


import pytest  # noqa: E402

from app.db import Base, init_schema  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    """Create all tables once for the test session."""
    init_schema()
    yield


@pytest.fixture(autouse=True)
def _clean_tables():
    """Remove all rows between tests so each test starts with a clean DB."""
    yield
    session = SessionLocal()
    # Truncate every table in reverse FK order for speed.
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    session.close()