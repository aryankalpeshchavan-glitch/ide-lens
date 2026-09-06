"""Tests for authentication boundaries, JWT verification, and user ownership isolation."""

import pytest
from fastapi.testclient import TestClient

from app.core.auth import create_access_token
from app.core.config import get_settings
from app.main import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


def test_public_health_endpoint_accessible_without_auth(client):
    """The /health endpoint must remain unconditionally public."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_jwt_issuance_and_session_introspection(client):
    """Token endpoint generates valid Bearer JWT that authenticates session."""
    res = client.post("/api/v1/auth/token", json={"user_id": "researcher-alice"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user_id"] == "researcher-alice"

    # Use token on /me
    token = data["access_token"]
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["user_id"] == "researcher-alice"


def test_auth_enforced_mode_blocks_unauthenticated_requests(monkeypatch):
    """When security_mode is enforced, unauthenticated requests are strictly rejected with 401."""
    settings = get_settings()
    monkeypatch.setattr(settings, "security_mode", "enforced")

    app = create_app()
    with TestClient(app) as auth_client:
        res = auth_client.post(
            "/api/v1/research-runs",
            json={"idea": "A quantum key distribution network using entangled photons."},
        )
        assert res.status_code == 401
        assert "Authentication required" in res.json()["detail"]


def test_ownership_isolation_between_users(client):
    """User B must not access or see User A's research runs or documents."""
    token_a = create_access_token("user-alice")
    token_b = create_access_token("user-bob")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Alice creates a run
    idea = "A novel neuromorphic architecture for low-power event camera processing."
    create_res = client.post("/api/v1/research-runs", json={"idea": idea}, headers=headers_a)
    assert create_res.status_code == 202
    run_id = create_res.json()["id"]

    # Alice can read her own run
    alice_read = client.get(f"/api/v1/research-runs/{run_id}", headers=headers_a)
    assert alice_read.status_code == 200

    # Bob CANNOT read Alice's run (returns 404 to avoid leaking existence)
    bob_read = client.get(f"/api/v1/research-runs/{run_id}", headers=headers_b)
    assert bob_read.status_code == 404

    # Bob's run list does NOT contain Alice's run
    bob_list = client.get("/api/v1/research-runs", headers=headers_b)
    assert bob_list.status_code == 200
    bob_run_ids = [r["id"] for r in bob_list.json()["items"]]
    assert run_id not in bob_run_ids

    # Alice's run list DOES contain her run
    alice_list = client.get("/api/v1/research-runs", headers=headers_a)
    assert alice_list.status_code == 200
    alice_run_ids = [r["id"] for r in alice_list.json()["items"]]
    assert run_id in alice_run_ids
