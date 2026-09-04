"""Idea collision analysis (ARCHITECTURE.md M-12).

Combination-level representation analysis over the retrieved corpus.
Under-represented combinations are flagged as investigation-worthy — never as
novel.
"""

from itertools import combinations

from app.analysis.common import tokens

_LANGUAGE = {
    "common": "The combination is well represented in the retrieved corpus.",
    "moderately_represented": "The combination appears in several retrieved items.",
    "limited_evidence_found": (
        "Limited evidence of this combination was found within the retrieved and "
        "analysed corpus."
    ),
    "insufficient_evidence": (
        "Insufficient evidence was retrieved to characterize this combination."
    ),
}


def compute_collisions(decomposition: dict, evidences: list[dict]) -> list[dict]:
    """Enumerate concept-pair combinations and their corpus representation."""
    concepts = list((decomposition or {}).get("concepts") or [])[:4]
    if len(concepts) < 2:
        return []

    text_tokens = [
        tokens(f"{e.get('claim_text', '')} {e.get('excerpt', '')}") for e in evidences
    ]
    results: list[dict] = []
    for left, right in combinations(concepts, 2):
        left_tokens = tokens(left)
        right_tokens = tokens(right)
        if not left_tokens or not right_tokens:
            continue
        matching = sum(
            1
            for doc in text_tokens
            if left_tokens <= doc and right_tokens <= doc
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
                "explanation": _LANGUAGE[level],
                "confidence": "medium" if matching >= 1 else "low",
            }
        )
    return results