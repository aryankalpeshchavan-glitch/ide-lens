"""Redis source cache for outbound query results.

Key format: idealens:source-cache:{adapter_id}:{sha256(query_text)}
Preserves:
- query
- source adapter id
- retrieval timestamp
- provenance identifiers
- full SourceItemData payload
"""

import hashlib
import json
import logging
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from app.core.config import get_settings
from app.infrastructure.redis import build_redis_client
from app.sources.base import SourceItemData

logger = logging.getLogger(__name__)


def compute_query_hash(query_text: str) -> str:
    """Compute stable, normalized SHA-256 hash for query string."""
    normalized = " ".join(query_text.strip().lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_cached_sources(adapter_id: str, query_text: str) -> list[SourceItemData] | None:
    """Retrieve cached source results if present and valid."""
    settings = get_settings()
    if not settings.source_cache_enabled:
        return None

    query_hash = compute_query_hash(query_text)
    key = f"idealens:source-cache:{adapter_id}:{query_hash}"

    try:
        client = build_redis_client()
        raw = client.get(key)
        client.close()
        if not raw:
            return None

        data = json.loads(raw if isinstance(raw, str) else raw.decode("utf-8"))
        items_raw = data.get("items", [])
        items: list[SourceItemData] = []
        for ir in items_raw:
            items.append(
                SourceItemData(
                    adapter_id=ir.get("adapter_id", adapter_id),
                    source_kind=ir.get("source_kind", "paper"),
                    title=ir.get("title", ""),
                    identifiers=ir.get("identifiers", {}),
                    authors=ir.get("authors", []),
                    venue=ir.get("venue"),
                    year=ir.get("year"),
                    abstract_or_description=ir.get("abstract_or_description"),
                    primary_url=ir.get("primary_url"),
                    quality_signals=ir.get("quality_signals", {}),
                    raw_payload=ir.get("raw_payload", {}),
                )
            )
        logger.info(
            "Source cache hit for %s on '%s' (%d items)",
            adapter_id,
            query_text[:40],
            len(items),
        )
        return items
    except Exception as exc:  # noqa: BLE001
        logger.debug("Source cache read skipped for %s: %s", key, exc)
        return None


def set_cached_sources(
    adapter_id: str,
    query_text: str,
    items: list[SourceItemData],
    ttl_seconds: int | None = None,
) -> bool:
    """Persist source items to Redis with stable hash and provenance."""
    settings = get_settings()
    if not settings.source_cache_enabled or not items:
        return False

    query_hash = compute_query_hash(query_text)
    key = f"idealens:source-cache:{adapter_id}:{query_hash}"
    ttl = ttl_seconds if ttl_seconds is not None else settings.source_cache_ttl_seconds

    payload: dict[str, Any] = {
        "adapter_id": adapter_id,
        "query": query_text,
        "query_hash": query_hash,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "items": [asdict(item) for item in items],
    }

    try:
        client = build_redis_client()
        serialized = json.dumps(payload)
        client.setex(key, ttl, serialized)
        client.close()
        logger.info(
            "Cached %d source items for %s query '%s'",
            len(items),
            adapter_id,
            query_text[:40],
        )
        return True
    except Exception as exc:  # noqa: BLE001
        logger.debug("Source cache write skipped for %s: %s", key, exc)
        return False
