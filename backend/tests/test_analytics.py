"""Unit tests for analytical engines, staged pipeline outputs, and scientific guardrails."""

import pytest
from fastapi.testclient import TestClient

from app.analysis.similarity import compute_similarity
from app.main import create_app
from app.reports.generator import check_language


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


_VALID_IDEA = (
    "A self-supervised geometric deep learning method for invariant molecular "
    "property prediction using equivariant graph neural networks and Hamiltonian dynamics."
)


def test_research_run_complete_lifecycle_and_analytics_endpoints(client):
    """Verify that a research run executes all stages and populates all endpoints."""
    # 1. Create run
    post_res = client.post("/api/v1/research-runs", json={"idea": _VALID_IDEA})
    assert post_res.status_code == 202
    run = post_res.json()
    run_id = run["id"]
    assert run["status"] in ("completed", "partially_failed")
    assert run["progress"] == 100
    assert run["decision_signal"] >= 50
    assert run["decomposition"] is not None
    assert "problem" in run["decomposition"]
    assert "objective" in run["decomposition"]

    # 2. Test similarity endpoint
    sim_res = client.get(f"/api/v1/research-runs/{run_id}/similarity")
    assert sim_res.status_code == 200
    sims = sim_res.json()
    assert isinstance(sims, list)
    for s in sims:
        assert "dimension" in s
        assert "score" in s
        assert "confidence" in s
        assert "Corpus-scoped signal" in s["explanation"]
        assert "100% novel" not in s["explanation"].lower()

    # 3. Test coverage endpoint
    cov_res = client.get(f"/api/v1/research-runs/{run_id}/coverage")
    assert cov_res.status_code == 200
    covs = cov_res.json()
    assert isinstance(covs, list)
    for c in covs:
        assert c["level"] in ("strong", "moderate", "limited", "insufficient")

    # 4. Test contradictions endpoint
    con_res = client.get(f"/api/v1/research-runs/{run_id}/contradictions")
    assert con_res.status_code == 200
    assert isinstance(con_res.json(), list)

    # 5. Test gaps endpoint
    gap_res = client.get(f"/api/v1/research-runs/{run_id}/gaps")
    assert gap_res.status_code == 200
    gaps = gap_res.json()
    assert isinstance(gaps, list)
    for g in gaps:
        assert g["saturation_bucket"] in (
            "common", "moderately_represented", "limited_evidence_found", "insufficient_evidence",
        )
        assert "novel" not in g["standardized_language"].lower()

    # 6. Test collisions endpoint
    col_res = client.get(f"/api/v1/research-runs/{run_id}/collisions")
    assert col_res.status_code == 200
    assert isinstance(col_res.json(), list)

    # 7. Test stress-test endpoint
    str_res = client.get(f"/api/v1/research-runs/{run_id}/stress-test")
    assert str_res.status_code == 200
    stresses = str_res.json()
    assert isinstance(stresses, list)
    for st in stresses:
        assert st["severity"] in ("low", "medium", "high", "critical")
        assert "recommendation" in st

    # 8. Test differentiation endpoint
    dif_res = client.get(f"/api/v1/research-runs/{run_id}/differentiation")
    assert dif_res.status_code == 200
    diffs = dif_res.json()
    assert isinstance(diffs, list)
    if diffs:
        rec = diffs[0]
        assert "differentiation_hypothesis" in rec
        assert "remaining_uncertainty" in rec
        assert "novelty" not in rec["differentiation_hypothesis"].lower()

    # 9. Test research graph endpoint
    graph_res = client.get(f"/api/v1/research-runs/{run_id}/graph")
    assert graph_res.status_code == 200
    graph = graph_res.json()
    assert "nodes" in graph
    assert "edges" in graph
    assert any(n["node_type"] == "idea" for n in graph["nodes"])

    # 10. Test traceable report endpoint
    rep_res = client.get(f"/api/v1/research-runs/{run_id}/report")
    assert rep_res.status_code == 200
    report = rep_res.json()
    assert "content" in report
    assert "# IdeaLens Research Report" in report["content"]
    assert report["language_guardrail_status"] == "passed"


def test_scientific_integrity_banned_phrases():
    """Verify that language guardrail strictly catches forbidden unscientific claims."""
    violations = check_language("Our model is 100% novel and outperforms all baselines.")
    assert "100% novel" in violations

    violations_first = check_language("This is the first ever architecture with no prior work.")
    assert "first ever" in violations_first
    assert "no prior work" in violations_first

    # Safe text must return empty violations
    safe_violations = check_language(
        "Limited evidence of this combination was found within the retrieved corpus."
    )
    assert len(safe_violations) == 0


def test_similarity_no_novelty_score():
    """Verify that compute_similarity produces per-dimension results, never a novelty score."""
    decomp = {
        "keywords": ["neural", "graph", "molecular"],
        "bigrams": ["neural network", "graph neural"],
        "concepts": ["graph neural"],
    }
    evidences = [
        {
            "id": "e1",
            "dimension": "technology",
            "excerpt": "A graph neural network for chemistry.",
            "claim_text": "Molecular property estimation",
        }
    ]
    results = compute_similarity(decomp, evidences)
    assert len(results) == 1
    assert results[0]["dimension"] == "technology"
    assert "Corpus-scoped signal, not a novelty judgment" in results[0]["explanation"]
