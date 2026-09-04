"""Tests for the research-run API contract.

With ``RUN_SYNC_EXECUTION=true`` (set in conftest.py) the POST endpoint
executes the full pipeline synchronously before returning, so tests can
assert on the completed run state.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

_IDEAS = {
    "valid": (
        "A privacy-preserving vector search engine for small teams that "
        "uses encrypted similarity to find relevant documents without "
        "exposing query content to the server."
    ),
}


@pytest.fixture
def client():
    return TestClient(create_app())


def test_create_research_run_returns_202_with_completed(client):
    """POST returns 202 and (because sync execution is on) a completed run."""
    response = client.post(
        "/api/v1/research-runs",
        json={"idea": _IDEAS["valid"]},
    )
    assert response.status_code == 202
    body = response.json()
    assert body["status"] in ("completed", "partially_failed")
    assert body["progress"] == 100
    assert body["idea"] == _IDEAS["valid"]
    assert "100% novel" not in body["disclosure"].lower()


def test_create_research_run_rejects_short_ideas(client):
    response = client.post(
        "/api/v1/research-runs", json={"idea": "too short"}
    )
    assert response.status_code == 422


def test_create_research_run_rejects_empty_idea(client):
    response = client.post("/api/v1/research-runs", json={"idea": ""})
    assert response.status_code == 422


def test_list_and_missing_research_run(client):
    response = client.get(
        "/api/v1/research-runs/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404
