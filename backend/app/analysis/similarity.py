"""Multidimensional similarity (SCORING.md §2).

Each dimension reports score + confidence + explanation + contributing
evidence ids. Without an embedding provider configured, the score is a hybrid
of lexical and structured (title/keyword) overlap — always disclosed in the
record. No aggregate "novelty" value is ever produced.
"""

from app.analysis.common import (
    average_overlap,
    clip01,
    confidence_label,
    jaccard,
    score_band,
    tokens,
)
from app.services.decomposition import _DIMENSION_CUES


def compute_similarity(decomposition: dict, evidences: list[dict]) -> list[dict]:
    """Compute per-dimension similarity over evidence records.

    ``evidences`` entries: ``{"id", "dimension", "excerpt", "claim_text", ...}``.
    """
    idea_keywords = set((decomposition or {}).get("keywords") or [])
    idea_bigrams = set((decomposition or {}).get("bigrams") or [])
    results: list[dict] = []

    by_dimension: dict[str, list[dict]] = {}
    for evidence in evidences:
        dimension = evidence.get("dimension") or "other"
        by_dimension.setdefault(dimension, []).append(evidence)

    for dimension, dimension_evidences in sorted(by_dimension.items()):
        if not dimension_evidences:
            continue
        reference_terms = idea_keywords | set(_DIMENSION_CUES.get(dimension, set()))
        ref_bigrams = idea_bigrams
        references = [tokens(e.get("excerpt", "")) for e in dimension_evidences]
        titles = [tokens(e.get("claim_text", "")) for e in dimension_evidences]

        # Lexical: how much of the idea's vocabulary shows up in evidence text.
        lexical = average_overlap(reference_terms, references)
        # Structured: overlap of idea bigram concepts with evidence titles.
        structured = average_overlap(ref_bigrams, titles)

        components: list[tuple[float | None, float]] = []
        if lexical is not None:
            components.append((lexical, 0.7))
        if structured is not None:
            components.append((structured, 0.3))

        if not components:
            continue
        weighted = sum(score * weight for score, weight in components) / sum(
            weight for _score, weight in components
        )
        score = round(clip01(weighted), 3)
        confidence = confidence_label(len(dimension_evidences))
        evidence_ids = [e["id"] for e in dimension_evidences]

        explanation = (
            f"{len(dimension_evidences)} retrieved item(s) address the '{dimension}' "
            f"dimension; lexical overlap {lexical:.2f}"
            + (f", structured overlap {structured:.2f}" if structured is not None else "")
            + f", band '{score_band(score)}'. Corpus-scoped signal, not a novelty judgment."
        )
        results.append(
            {
                "dimension": dimension,
                "score": score,
                "confidence": confidence,
                "explanation": explanation,
                "evidence_ids": [str(x) for x in evidence_ids],
                "lexical_score": lexical,
                "structured_score": structured,
                "embedding_score": None,
            }
        )
    return results


def jaccard_concept_overlap(text_a: str, text_b: str) -> float:
    """Expose Jaccard for concept-overlap callers (collisions/stress)."""
    return jaccard(tokens(text_a), tokens(text_b))