"""Idea collision analysis (ARCHITECTURE.md M-12 & RESEARCH QUALITY §2.3).

Combination-level representation analysis over technical components across the retrieved corpus.
Under-represented combinations are flagged as investigation-worthy — never claimed as novel.
"""

from itertools import combinations

from app.analysis.common import tokens

_EXPLANATIONS = {
    "common": (
        "This technical combination has extensive precedent in the literature. "
        "Standard integration patterns and established baseline comparisons exist."
    ),
    "moderately_represented": (
        "Emerging intersection: several works explore this combination. Trade-offs "
        "between algorithmic complexity, runtime latency, and robustness remain "
        "actively researched."
    ),
    "limited_evidence_found": (
        "Sparse co-occurrence found within the analyzed corpus. This combination represents an "
        "investigation-worthy architectural boundary where integration assumptions should "
        "be empirically validated."
    ),
    "insufficient_evidence": (
        "Insufficient co-occurring evidence was retrieved for this technical pair. Worth "
        "verifying whether theoretical barriers, evaluation difficulty, or deployment constraints "
        "explain the sparse literature."
    ),
}


def compute_collisions(decomposition: dict, evidences: list[dict]) -> list[dict]:
    """Enumerate genuine technical component combinations and assess corpus representation."""
    # Prioritize technical_components over generic concepts
    raw_components = (
        (decomposition or {}).get("technical_components")
        or (decomposition or {}).get("concepts")
        or []
    )
    # Ensure items are clean multi-word technical components
    components = [str(c).strip() for c in raw_components if len(str(c).strip()) > 3][:5]
    if len(components) < 2:
        return []

    text_tokens = [
        tokens(f"{e.get('claim_text', '')} {e.get('excerpt', '')}") for e in evidences
    ]
    results: list[dict] = []

    for left, right in combinations(components, 2):
        left_tokens = tokens(left)
        right_tokens = tokens(right)
        if not left_tokens or not right_tokens:
            continue

        # Count evidence documents containing key tokens from both components
        matching = sum(
            1
            for doc in text_tokens
            if (left_tokens & doc) and (right_tokens & doc)
        )

        level = (
            "common"
            if matching >= 3
            else "moderately_represented"
            if matching == 2
            else "limited_evidence_found"
            if matching == 1
            else "insufficient_evidence"
        )

        results.append(
            {
                "component_ids": [left, right],
                "level": level,
                "evidence_count": matching,
                "explanation": _EXPLANATIONS[level],
                "confidence": (
                    "high" if matching >= 3 else "medium" if matching >= 1 else "low"
                ),
            }
        )
    return results