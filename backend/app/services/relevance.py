"""Source relevance scoring and technical candidate filtering (RESEARCH QUALITY §2.2).

Ranks retrieved papers and repositories using technical domain signals:
- Title concept overlap
- Abstract / description technical terminology match
- Method, technology, problem cue alignment
- Venue and citation signals where present
Down-ranks and filters irrelevant noise before evidence extraction.
"""


from app.analysis.common import tokens
from app.sources.base import SourceItemData

_STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "with", "into", "from", "using",
    "that", "this", "these", "those", "which", "will", "can", "would", "should",
    "over", "under", "through", "between", "among", "our", "their", "its",
    "about", "such", "each", "also", "been", "was", "were", "have", "has",
    "paper", "present", "propose", "study", "approach", "method", "based",
}


def _extract_technical_terms(text: str) -> set[str]:
    """Extract distinctive technical word tokens (len > 3, non-stopwords)."""
    raw_tokens = tokens(text)
    return {t for t in raw_tokens if t not in _STOPWORDS and len(t) > 3}


def score_source_relevance(
    item: SourceItemData,
    target_terms: set[str],
    idea_text: str = "",
) -> float:
    """Calculate a normalized technical relevance score [0.0, 1.0]."""
    if not target_terms:
        return 0.5  # Neutral default if no target terms given

    title_text = item.title or ""
    desc_text = item.abstract_or_description or ""

    title_tokens = _extract_technical_terms(title_text)
    desc_tokens = _extract_technical_terms(desc_text)

    # 1. Title match (highest signal)
    title_overlap = len(title_tokens & target_terms)
    title_score = min(1.0, title_overlap / max(1, min(4, len(target_terms))))

    # 2. Abstract / Description match
    desc_overlap = len(desc_tokens & target_terms)
    desc_score = min(1.0, desc_overlap / max(1, min(8, len(target_terms))))

    # 3. Quality signals boost
    quality_boost = 0.0
    year = item.year
    if year and year >= 2018:
        quality_boost += 0.05
    if item.primary_url:
        quality_boost += 0.05
    if item.venue:
        quality_boost += 0.05

    # Weighted combination
    composite = (title_score * 0.55) + (desc_score * 0.35) + quality_boost
    return round(min(1.0, composite), 3)


def rank_and_filter_sources(
    items: list[SourceItemData],
    idea: str,
    *,
    min_threshold: float = 0.05,
    max_candidates: int = 40,
) -> list[SourceItemData]:
    """Score, annotate, sort, and filter candidate source items by technical relevance."""
    target_terms = _extract_technical_terms(idea)
    if not items:
        return []

    scored_items: list[tuple[float, SourceItemData]] = []
    for item in items:
        score = score_source_relevance(item, target_terms, idea)
        # Record relevance score in item quality signals
        signals = dict(item.quality_signals or {})
        signals["relevance_score"] = score
        item.quality_signals = signals
        scored_items.append((score, item))

    # Sort descending by relevance score
    scored_items.sort(key=lambda x: x[0], reverse=True)

    # Filter out items below threshold unless the total corpus would become too empty
    filtered = [item for score, item in scored_items if score >= min_threshold]
    if not filtered and scored_items:
        # Keep the top few even if low score rather than completely zeroing out
        filtered = [item for _, item in scored_items[:5]]

    return filtered[:max_candidates]
