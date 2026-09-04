"""Retrieval orchestration (ARCHITECTURE.md M-5).

Fans queries out across source adapters with a global concurrency cap, isolates
per-source failures, and returns normalized items plus failure records. Rate
limiting and retries live in the HTTP layer; caching is added here later.
"""

import asyncio
import logging

from app.sources.http import PermanentSourceError, TransientSourceError

logger = logging.getLogger(__name__)


async def run_retrieval(
    registry,
    queries: list[dict],
    *,
    limit: int,
    semaphore: asyncio.Semaphore,
) -> tuple[list, list[dict]]:
    """Search all adapters for all queries.

    Returns (items, failures) where items are adapter ``SourceItemData``
    results tagged with their adapter id, and failures are per-(adapter, query)
    records for the run's coverage disclosure.
    """
    adapters = registry.all()
    if not adapters or not queries:
        return [], []

    async def search_one(adapter, query: dict) -> tuple[list, list[dict]]:
        async with semaphore:
            try:
                items = await adapter.search(query["query_text"], limit=limit)
                return items, []
            except (TransientSourceError, PermanentSourceError) as exc:
                failure = {
                    "adapter_id": adapter.adapter_id,
                    "query": query["query_text"],
                    "error": str(exc)[:300],
                    "class": _class_of(exc),
                }
                return [], [failure]
            except Exception as exc:  # noqa: BLE001 - isolate unexpected adapter failures
                logger.exception("Unexpected failure in adapter %s", adapter.adapter_id)
                failure = {
                    "adapter_id": adapter.adapter_id,
                    "query": query["query_text"],
                    "error": str(exc)[:300],
                    "class": "UNEXPECTED",
                }
                return [], [failure]

    outcomes = await asyncio.gather(
        *[search_one(adapter, query) for query in queries for adapter in adapters]
    )

    items: list = []
    failures: list[dict] = []
    for item_batch, failure_batch in outcomes:
        items.extend(item_batch)
        failures.extend(failure_batch)
    return items, failures


def _class_of(exc: BaseException) -> str:
    if isinstance(exc, TransientSourceError):
        return "HTTP_TRANSIENT"
    if isinstance(exc, PermanentSourceError):
        return "HTTP_4XX"
    return "UNEXPECTED"