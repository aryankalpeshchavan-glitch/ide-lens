"""Evidence extraction (ARCHITECTURE.md M-7, EVIDENCE_MODEL.md).

The default extractor is deterministic and derives evidence strictly from
stored source metadata (title, abstract/description, identifiers) — it never
invents passages. An AI provider can be plugged in later to add LLM-based
dimension classification without changing the evidence schema.
"""

import re

from app.core.config import get_settings
from app.services.decomposition import _DIMENSION_CUES

_WORD_RE = re.compile(r"[a-z]{3,}")


def detect_dimension(text: str) -> str:
    """Classify a passage into an evidence dimension using cue vocabulary."""
    words = _WORD_RE.findall(text.lower())
    best_dimension, best_score = "other", 0
    for dimension, cues in _DIMENSION_CUES.items():
        score = sum(1 for word in words if word in cues)
        if score > best_score:
            best_dimension, best_score = dimension, score
    return best_dimension


def _first_sentence(text: str) -> str:
    cleaned = " ".join(text.split())
    match = re.split(r"(?<=[.!?])\s+", cleaned, maxsplit=1)
    return match[0] if match else cleaned


def _cap_excerpt(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def compute_strength(source: dict) -> str:
    """Composed evidence strength: provenance completeness + content presence."""
    has_identifier = bool(source.get("identifiers"))
    has_abstract = bool(source.get("abstract_or_description"))
    has_year = bool(source.get("year"))
    score = sum([has_identifier, has_abstract, has_year])
    if score >= 2 and has_identifier:
        return "strong"
    if source.get("quality_signals", {}).get("stars") is not None or score >= 1:
        return "moderate"
    return "weak"


def extract_evidence(
    sources: list[dict],
    decomposition: dict,
    *,
    excerpt_limit: int | None = None,
) -> list[dict]:
    """Build evidence records from normalized canonical source items."""
    settings = get_settings()
    limit = excerpt_limit or settings.excerpt_char_limit
    records: list[dict] = []
    idea_dimensions = list((decomposition or {}).get("dimensions", {}).keys())

    for item in sources:
        title = item.get("title") or ""
        abstract = item.get("abstract_or_description") or ""
        body = abstract or title
        dimension = detect_dimension(f"{title} {body}")
        identifiers = item.get("identifiers") or {}
        primary_url = item.get("primary_url")

        excerpt_body = abstract[:limit] if abstract else title
        excerpt = _cap_excerpt(excerpt_body or title, limit)

        claim_text = _first_sentence(abstract) if abstract else f"Related work: {title}"
        records.append(
            {
                "source_item_id": item["id"],
                "dimension": dimension if dimension != "other" else (
                    idea_dimensions[0] if idea_dimensions else "other"
                ),
                "claim_text": claim_text,
                "excerpt": excerpt,
                "excerpt_span": {"offset": 0, "length": len(excerpt)} if abstract else None,
                "extraction_confidence": "medium",
                "provenance_backref": {
                    "identifiers": identifiers,
                    "url": primary_url,
                    "title": title,
                },
                "created_by": "deterministic.metadata-v1",
                "strength": compute_strength(item),
            }
        )
    return records