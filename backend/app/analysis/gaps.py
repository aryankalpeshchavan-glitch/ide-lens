"""Gap analysis (SCORING.md §5–6).

Gap signals are evidence-based observations that a combination or dimension is
less represented in the retrieved corpus — never a novelty claim. Required
standardized phrasing is enforced by the bucket language below.
"""

from itertools import combinations

from app.analysis.common import tokens

_LANGUAGE = {
    "common": "This area is well represented within the retrieved and analysed corpus.",
    "moderately_represented": (
        "This area is moderately represented within the retrieved and analysed corpus."
    ),
    "limited_evidence_found": (
        "Limited evidence of this combination was found within the retrieved and "
        "analysed corpus."
    ),
    "insufficient_evidence": (
        "Insufficient evidence was retrieved to characterize this area; the corpus "
        "does not support a stronger statement."
    ),
}


def compute_gaps(
    decomposition: dict,
    evidences: list[dict],
    coverage_results: list[dict],
    *,
    queries_planned: int = 1,
    queries_executed: int = 1,
) -> list[dict]:
    """Return research-gap records (dimension-level + concept-combination)."""
    gaps: list[dict] = []
    coverage_disclosure = {
        "queries_planned": queries_planned,
        "queries_executed": queries_executed,
        "coverage_degraded": queries_executed < queries_planned,
    }

    for coverage in coverage_results:
        if coverage["level"] in ("limited", "insufficient"):
            bucket = (
                "limited_evidence_found"
                if coverage["level"] == "limited"
                else "insufficient_evidence"
            )
            gaps.append(
                {
                    "scope_kind": "dimension",
                    "subject": {"dimension": coverage["dimension"]},
                    "saturation_bucket": bucket,
                    "standardized_language": _LANGUAGE[bucket],
                    "coverage_disclosure": coverage_disclosure,
                    "evidence_basis": {
                        "evidence_ids": [
                            str(e["id"])
                            for e in evidences
                            if e.get("dimension") == coverage["dimension"]
                        ],
                        "evidence_count": coverage["evidence_count"],
                    },
                }
            )

    evidence_tokens = [
        (e, tokens(f"{e.get('claim_text', '')} {e.get('excerpt', '')}")) for e in evidences
    ]
    concepts = list((decomposition or {}).get("concepts") or [])[:5]
    for left, right in combinations(concepts, 2):
        left_tokens = tokens(left)
        right_tokens = tokens(right)
        if not left_tokens or not right_tokens:
            continue
        matching = []
        for evidence, text_tokens in evidence_tokens:
            if left_tokens <= text_tokens and right_tokens <= text_tokens:
                matching.append(evidence["id"])
        bucket = (
            "common"
            if len(matching) >= 3
            else "limited_evidence_found"
            if matching
            else "insufficient_evidence"
        )
        gaps.append(
            {
                "scope_kind": "combination",
                "subject": {"components": [left, right]},
                "saturation_bucket": bucket,
                "standardized_language": _LANGUAGE[bucket],
                "coverage_disclosure": coverage_disclosure,
                "evidence_basis": {"evidence_ids": [str(x) for x in matching]},
            }
        )
    return gaps