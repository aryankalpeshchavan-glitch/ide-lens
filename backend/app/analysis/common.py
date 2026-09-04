"""Shared helpers for analysis modules (tokenization, bands, confidence)."""

import re

_WORD_RE = re.compile(r"[a-z]{3,}")


def tokens(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def jaccard(left: set[str], right: set[str]) -> float:
    """Jaccard overlap; returns 0.0 when either set is empty."""
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def average_overlap(reference: set[str], documents: list[set[str]]) -> float | None:
    """Average fraction of ``reference`` tokens present in each document."""
    if not reference or not documents:
        return None
    ratio = 0.0
    for doc in documents:
        if doc:
            ratio += len(reference & doc) / len(reference)
    return ratio / len(documents)


def confidence_label(count: int, *, threshold_high: int = 5, threshold_medium: int = 2) -> str:
    """Map an evidence count to a confidence label."""
    if count >= threshold_high:
        return "high"
    if count >= threshold_medium:
        return "medium"
    return "low"


def score_band(score: float | None) -> str:
    """Display band for a score (SCORING.md §2); bands are aids only."""
    if score is None:
        return "none"
    if score >= 0.8:
        return "very_high"
    if score >= 0.6:
        return "high"
    if score >= 0.4:
        return "moderate"
    if score >= 0.2:
        return "low"
    return "very_low"


def clip01(value: float) -> float:
    return max(0.0, min(1.0, value))