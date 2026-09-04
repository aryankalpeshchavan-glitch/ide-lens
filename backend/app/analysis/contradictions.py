"""Contradiction detection (SCORING.md §7).

Deterministic pre-checks run before any summarization: same-dimension evidence
pairs are tested for opposing lexical signals on a shared subject. Both sides
are always preserved; when protocols differ the discrepancy is labeled
``not_directly_comparable`` instead of scored as a contradiction.
"""

from itertools import combinations

from app.analysis.common import tokens

_POSITIVE = {
    "improve", "improves", "outperform", "outperforms", "reduce", "reduces", "increase",
    "increases", "enable", "enables", "efficient", "stable", "better", "works",
    "state-of-the-art", "accurate",
}
_NEGATIVE = {
    "fail", "fails", "cannot", "unstable", "degrade", "degrades", "worse", "limitation",
    "limitations", "issues", "inconsistent", "unreliable", "not", "no evidence",
    "struggles", "expensive",
}


def _signal(text: str) -> int:
    found = tokens(text) & (_POSITIVE | _NEGATIVE)
    score = 0
    for mark in found:
        if mark in _POSITIVE:
            score += 1
        elif mark in _NEGATIVE:
            score -= 1
    return score


def compute_contradictions(evidences: list[dict], sources: dict) -> list[dict]:
    """Detect opposing-signal evidence pairs on a shared subject.

    ``sources`` maps source_item_id -> {venue, ...} for comparability checks.
    """
    results: list[dict] = []
    by_dimension: dict[str, list[dict]] = {}
    for evidence in evidences:
        by_dimension.setdefault(evidence.get("dimension") or "other", []).append(evidence)

    for dimension, items in by_dimension.items():
        for left, right in combinations(items, 2):
            if left.get("source_item_id") == right.get("source_item_id"):
                continue
            subject = _shared_subject(left, right)
            if not subject:
                continue
            left_signal = _signal(f"{left.get('claim_text', '')} {left.get('excerpt', '')}")
            right_signal = _signal(f"{right.get('claim_text', '')} {right.get('excerpt', '')}")
            if left_signal == 0 or right_signal == 0 or (left_signal > 0) == (right_signal > 0):
                continue

            left_source = sources.get(left.get("source_item_id")) or {}
            right_source = sources.get(right.get("source_item_id")) or {}
            comparable = (
                bool(left_source.get("venue"))
                and left_source.get("venue") == right_source.get("venue")
            )
            results.append(
                {
                    "dimension": dimension,
                    "subject": subject,
                    "evidence_a_id": left["id"],
                    "evidence_b_id": right["id"],
                    "source_a_id": left.get("source_item_id"),
                    "source_b_id": right.get("source_item_id"),
                    "comparability": "comparable" if comparable else "not_directly_comparable",
                    "conflict_summary": (
                        f"Two retrieved items diverge in emphasis on '{subject}'. Both "
                        "sides are preserved; neither is selected as the winner."
                    ),
                    "possible_explanations": [
                        "Different datasets, evaluation protocols, metrics, or "
                        "experimental conditions."
                    ],
                    "confidence": "medium",
                }
            )
            if len(results) >= 20:
                return results
    return results


def _shared_subject(left: dict, right: dict) -> str:
    left_tokens = tokens(f"{left.get('claim_text', '')} {left.get('excerpt', '')}")
    right_tokens = tokens(f"{right.get('claim_text', '')} {right.get('excerpt', '')}")
    shared = (left_tokens & right_tokens) - (_POSITIVE | _NEGATIVE)
    for candidate in _SUBJECT_PRIORITY:
        if candidate in shared:
            return candidate
    if shared:
        return max(shared, key=len)
    return ""


_SUBJECT_PRIORITY = (
    "attention", "forecasting", "noise", "training", "dataset", "accuracy", "latency",
    "transformer", "scalability", "privacy", "efficiency", "memory", "optimization",
)