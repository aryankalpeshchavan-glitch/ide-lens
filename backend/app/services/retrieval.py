"""Retrieval orchestration (ARCHITECTURE.md M-5).

Fans queries out across source adapters with bounded concurrency, utilizes
Redis source caching with stable query hashing, isolates per-source failures,
and ranks retrieved sources by technical domain relevance.
"""

import asyncio
import logging

from app.infrastructure.cache import get_cached_sources, set_cached_sources
from app.services.relevance import rank_and_filter_sources
from app.sources.base import SourceItemData
from app.sources.http import PermanentSourceError, TransientSourceError

logger = logging.getLogger(__name__)


async def run_retrieval(
    registry,
    queries: list[dict],
    *,
    limit: int,
    semaphore: asyncio.Semaphore,
    idea: str = "",
) -> tuple[list[SourceItemData], list[dict]]:
    """Search all adapters for all queries with caching and relevance ranking.

    Returns (items, failures) where items are adapter ``SourceItemData``
    results tagged with their adapter id, and failures are per-(adapter, query)
    records for the run's coverage disclosure.
    """
    adapters = registry.all()
    if not adapters or not queries:
        return [], []

    async def search_one(adapter, query: dict) -> tuple[list[SourceItemData], list[dict]]:
        query_text = query["query_text"]

        # 1. Check Redis cache first
        cached = get_cached_sources(adapter.adapter_id, query_text)
        if cached is not None:
            return cached, []

        # 2. Concurrency-bounded adapter fetch
        async with semaphore:
            try:
                items = await adapter.search(query_text, limit=limit)
                if items:
                    set_cached_sources(adapter.adapter_id, query_text, items)
                return items, []
            except (TransientSourceError, PermanentSourceError) as exc:
                failure = {
                    "adapter_id": adapter.adapter_id,
                    "query": query_text,
                    "error": str(exc)[:300],
                    "class": _class_of(exc),
                }
                return [], [failure]
            except Exception as exc:  # noqa: BLE001 - isolate unexpected adapter failures
                logger.exception("Unexpected failure in adapter %s", adapter.adapter_id)
                failure = {
                    "adapter_id": adapter.adapter_id,
                    "query": query_text,
                    "error": str(exc)[:300],
                    "class": "UNEXPECTED",
                }
                return [], [failure]

    outcomes = await asyncio.gather(
        *[search_one(adapter, query) for query in queries for adapter in adapters]
    )

    items: list[SourceItemData] = []
    failures: list[dict] = []
    for item_batch, failure_batch in outcomes:
        items.extend(item_batch)
        failures.extend(failure_batch)

    # 3. Score and rank candidates by technical relevance
    if idea:
        items = rank_and_filter_sources(items, idea)

    return items, failures


def _class_of(exc: BaseException) -> str:
    if isinstance(exc, TransientSourceError):
        return "HTTP_TRANSIENT"
    if isinstance(exc, PermanentSourceError):
        return "HTTP_4XX"
    return "UNEXPECTED"