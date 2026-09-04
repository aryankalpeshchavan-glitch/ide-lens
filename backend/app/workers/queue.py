"""Redis-backed research job queue (ADR-0003).

The API enqueues run ids; the worker process consumes them. When Redis is
unreachable, the dispatcher falls back to the in-process executor so local
development still works.
"""

import logging
from uuid import UUID

from app.core.config import get_settings
from app.infrastructure.redis import build_redis_client

logger = logging.getLogger(__name__)


def enqueue_run(run_id: UUID) -> bool:
    """Push a run id onto the Redis queue; returns False when Redis is unavailable."""
    settings = get_settings()
    try:
        client = build_redis_client()
        client.rpush(settings.queue_key, str(run_id))
        client.close()
        logger.info("Enqueued run %s", run_id)
        return True
    except Exception:  # noqa: BLE001 - fallback policy is intentional
        logger.warning("Redis unavailable; run %s not enqueued", run_id)
        return False


def dequeue_run() -> str | None:
    """Block briefly for a job; returns the run id string or None on timeout."""
    settings = get_settings()
    try:
        client = build_redis_client()
        result = client.blpop(settings.queue_key, timeout=settings.queue_block_seconds)
        if result is None:
            return None
        return str(result[1])
    except Exception:  # noqa: BLE001 - worker loop must survive Redis outages
        logger.warning("Redis unavailable; worker idle")
        return None