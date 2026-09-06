"""Tests for research quality, query generation, technical extraction, and collision analysis."""

from app.analysis.collisions import compute_collisions
from app.services.decomposition import extract_technical_components
from app.services.query_planning import plan_queries


def test_query_generation_prioritizes_technical_dimensions():
    """Queries must contain concrete technical signals, not generic word fragments."""
    idea = (
        "A neurosymbolic reasoning system that integrates knowledge graphs with "
        "autonomous agents for multi-hop verification in clinical trials."
    )
    queries = plan_queries(idea)
    assert len(queries) >= 3

    purposes = {q["purpose"] for q in queries}
    assert "core" in purposes
    assert any(p in purposes for p in ("technology", "method", "problem", "combination"))

    for q in queries:
        text = q["query_text"]
        # Ensure query is not a single generic stopword or empty fragment
        assert len(text.split()) >= 1
        assert "technical scientific" not in text.lower()


def test_technical_component_extraction_filters_generic_bigrams():
    """Extraction must isolate genuine technical compound terms and reject generic fragments."""
    idea = (
        "We propose a novel technical scientific framework using neurosymbolic reasoning "
        "and knowledge graphs with multi-hop verification for autonomous agents."
    )
    components = extract_technical_components(idea)

    # Must extract genuine technical units
    components_lower = [c.lower() for c in components]
    assert any("neurosymbolic" in c for c in components_lower)
    assert any("knowledge graph" in c for c in components_lower)
    assert any("multi-hop" in c or "verification" in c for c in components_lower)

    # Must NOT extract generic adjacent fragments
    assert "technical scientific" not in components_lower
    assert "novel technical" not in components_lower
    assert "propose a" not in components_lower


def test_collision_analysis_operates_on_technical_components_without_novelty_claim():
    """Collision analysis assesses combinations without making false novelty guarantees."""
    decomposition = {
        "technical_components": [
            "neurosymbolic reasoning",
            "knowledge graphs",
            "multi-hop verification",
            "autonomous agents",
        ]
    }
    mock_evidences = [
        {
            "claim_text": (
                "Neurosymbolic reasoning incorporates knowledge graphs for structured deduction."
            ),
            "excerpt": "We combine neurosymbolic reasoning with curated knowledge graphs.",
        }
    ]

    collisions = compute_collisions(decomposition, mock_evidences)
    assert len(collisions) >= 1

    valid_levels = {
        "common", "moderately_represented", "limited_evidence_found", "insufficient_evidence"
    }
    for col in collisions:
        assert len(col["component_ids"]) == 2
        assert col["level"] in valid_levels
        assert "confidence" in col
        explanation = col["explanation"].lower()
        # Strictly verify no universal novelty claims
        assert "novelty score" not in explanation
        assert "100% novel" not in explanation
        assert "universally novel" not in explanation
