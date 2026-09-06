"""Redis-backed reliable research job queue (ADR-0003 & Production Hardening).

Implements the reliable processing pattern:
  queue -> processing -> acknowledgement -> completed

Workers atomically pop from the pending queue and push to a processing queue
(via RPOPLPUSH / LMOVE). If a worker process terminates abruptly before calling
`ack_run()`, the job remains in the processing queue and is recovered by stale-job
detection rather than lost permanently.
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
        logger.info("Enqueued run %s to %s", run_id, settings.queue_key)
        return True
    except Exception as exc:  # noqa: BLE001 - fallback policy is intentional
        logger.warning("Redis unavailable; run %s not enqueued (%s)", run_id, exc)
        return False


def dequeue_run_reliable(timeout: int | None = None) -> str | None:
    """Atomically claim a job from queue to processing list.

    Returns the run id string or None on timeout/outage.
    """
    settings = get_settings()
    block_sec = timeout if timeout is not None else settings.queue_block_seconds
    try:
        client = build_redis_client()
        # brpoplpush atomically moves item from queue_key to queue_processing_key
        # Compatible across Redis 2.2 through 7+
        result = client.brpoplpush(
            settings.queue_key,
            settings.queue_processing_key,
            timeout=block_sec,
        )
        client.close()
        if result is None:
            return None
        run_id_str = result.decode("utf-8") if isinstance(result, bytes) else str(result)
        logger.info("Reliably claimed run %s into processing queue", run_id_str)
        return run_id_str
    except Exception as exc:  # noqa: BLE001 - worker loop survives Redis outages
        logger.warning("Redis dequeue error: %s; worker idle", exc)
        return None


# Backward-compatible alias for existing callers
dequeue_run = dequeue_run_reliable


def ack_run(run_id: str | UUID) -> bool:
    """Acknowledge completion or handled failure, removing the run from processing queue."""
    settings = get_settings()
    run_id_str = str(run_id)
    try:
        client = build_redis_client()
        removed = client.lrem(settings.queue_processing_key, 0, run_id_str)
        client.close()
        logger.info("Acknowledged run %s (removed %s from processing queue)", run_id_str, removed)
        return True
    except Exception as exc:
        logger.warning("Failed to acknowledge run %s on Redis: %s", run_id_str, exc)
        return False


def move_to_dlq(run_id: str | UUID, reason: str = "max_retries_exceeded") -> bool:
    """Evacuate unrecoverable run to Dead Letter Queue for operator inspection."""
    settings = get_settings()
    run_id_str = str(run_id)
    try:
        client = build_redis_client()
        client.lrem(settings.queue_processing_key, 0, run_id_str)
        client.rpush(settings.queue_dlq_key, f"{run_id_str}:{reason}")
        client.close()
        logger.error("Run %s moved to DLQ: %s", run_id_str, reason)
        return True
    except Exception as exc:
        logger.warning("Failed to move run %s to DLQ: %s", run_id_str, exc)
        return False


def re_enqueue_stale_job(run_id: str | UUID) -> bool:
    """Re-enqueue a crashed worker's job from processing back to pending queue."""
    settings = get_settings()
    run_id_str = str(run_id)
    try:
        client = build_redis_client()
        pipe = client.pipeline()
        pipe.lrem(settings.queue_processing_key, 0, run_id_str)
        pipe.rpush(settings.queue_key, run_id_str)
        pipe.execute()
        client.close()
        logger.info("Re-enqueued stale run %s from processing to main queue", run_id_str)
        return True
    except Exception as exc:
        logger.warning("Failed to re-enqueue run %s: %s", run_id_str, exc)
        return False