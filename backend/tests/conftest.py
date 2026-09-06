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
os.environ.setdefault("HTTP_TIMEOUT_SECONDS", "2.0")
os.environ.setdefault("HTTP_MAX_RETRIES", "1")


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


@pytest.fixture(autouse=True)
def _mock_external_retrieval(monkeypatch):
    """Prevent slow outbound HTTP calls to external academic APIs during test runs."""
    async def mock_run_retrieval(registry, queries, *, limit, semaphore, idea=""):
        from app.sources.base import SourceItemData
        sample_items = [
            SourceItemData(
                adapter_id="arxiv",
                source_kind="paper",
                title="Graph Neural Networks with Equivariant Geometry",
                identifiers={"arxiv_id": "2106.12345", "doi": "10.1234/gnn.2021"},
                authors=["J. Doe", "A. Smith"],
                year=2021,
                abstract_or_description=(
                    "We investigate equivariant graph neural networks and Hamiltonian "
                    "dynamics for invariant molecular property prediction."
                ),
                primary_url="https://arxiv.org/abs/2106.12345",
                quality_signals={"citation_count": 42},
            ),
            SourceItemData(
                adapter_id="github",
                source_kind="repository",
                title="geometry-gnn-molecular",
                identifiers={"repo": "testorg/geometry-gnn-molecular"},
                authors=["testorg"],
                year=2022,
                abstract_or_description=(
                    "Open-source implementation of equivariant graph networks for "
                    "molecular dynamics simulation and property prediction."
                ),
                primary_url="https://github.com/testorg/geometry-gnn-molecular",
                quality_signals={"stars": 128},
            ),
        ]
        return sample_items, []

    monkeypatch.setattr("app.services.orchestrator.run_retrieval", mock_run_retrieval)