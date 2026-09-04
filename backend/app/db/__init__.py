"""Database infrastructure.

Provides the declarative ``Base``, the SQLAlchemy engine, and the session
factory. PostgreSQL is the production driver; SQLite is fully supported for
local development and the test-suite. Creating the engine does **not** open a
connection — the application boots even when PostgreSQL is not running.
"""

from app.db.base import Base
from app.db.session import SessionLocal, build_engine, engine, get_session, init_schema

__all__ = ["Base", "SessionLocal", "build_engine", "engine", "get_session", "init_schema"]