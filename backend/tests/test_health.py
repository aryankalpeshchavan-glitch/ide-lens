"""Tests for the /health endpoint.

Dependency probes are monkeypatched so the tests never require a real
PostgreSQL or Redis instance.
"""

from fastapi.testclient import TestClient

from app import __version__
from app.main import create_app


def _patch_probes(monkeypatch, database: str, redis: str) -> TestClient:
    """Patch the /health dependency probes and return an isolated app client."""
    from app.api.routes import health as health_module

    monkeypatch.setattr(health_module, "check_database_connection", lambda: database)
    monkeypatch.setattr(health_module, "check_redis_connection", lambda: redis)
    return TestClient(create_app())


def test_health_reports_ok_when_dependencies_healthy(monkeypatch):
    client = _patch_probes(monkeypatch, database="ok", redis="ok")

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "IdeaLens API"
    assert body["environment"] == "development"
    assert body["version"] == __version__
    assert body["dependencies"]["postgres"]["status"] == "ok"
    assert body["dependencies"]["redis"]["status"] == "ok"


def test_health_process_ok_while_dependencies_unavailable(monkeypatch):
    """Process health must be distinct from dependency health."""
    client = _patch_probes(monkeypatch, database="unavailable", redis="unavailable")

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"  # the API process itself is healthy
    assert body["dependencies"]["postgres"]["status"] == "unavailable"
    assert body["dependencies"]["redis"]["status"] == "unavailable"


def test_health_dependency_statuses_are_never_inferred(monkeypatch):
    """A dependency must not be reported healthy without a successful probe."""
    client = _patch_probes(monkeypatch, database="ok", redis="unavailable")

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["dependencies"]["postgres"]["status"] == "ok"
    assert body["dependencies"]["redis"]["status"] == "unavailable"