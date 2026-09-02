"""Redis configuration boundary.

M1 scope: configuration only. No queues, pub/sub, caching, workers, or retry
queues are implemented — those belong to later milestones. A cheap client
factory is provided for the /health redis probe and as the infrastructure
boundary future milestones will use.
"""

import logging

from redis import Redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def build_redis_client() -> Redis:
    """Create a Redis client from the configured ``REDIS_URL``.

    Building a client does not connect to Redis; the application boots whether
    or not Redis is running.
    """
    settings = get_settings()
    return Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=settings.dependency_check_timeout_seconds,
        socket_timeout=settings.dependency_check_timeout_seconds,
    )


def check_redis_connection() -> str:
    """Probe Redis connectivity (``PING``).

    Returns ``"ok"`` when the ping succeeds, otherwise ``"unavailable"``. The
    probe never raises.
    """
    try:
        build_redis_client().ping()
        return "ok"
    except Exception as exc:  # noqa: BLE001 - a probe must never raise
        logger.warning("Redis health probe failed: %s", exc)
        return "unavailable"