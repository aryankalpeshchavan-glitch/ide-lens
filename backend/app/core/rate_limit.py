"""Application-level rate limiting for expensive API endpoints.

Implements a sliding-window counter backed by Redis when reachable, with an
in-memory fallback when Redis is absent (development / standalone).
"""

import logging
import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

from app.core.config import get_settings
from app.infrastructure.redis import build_redis_client

logger = logging.getLogger(__name__)

# In-memory sliding window store: { "scope:client_ip": [timestamps] }
_MEM_LIMITS: dict[str, list[float]] = defaultdict(list)


class RateLimiter:
    """FastAPI route dependency enforcing rate limits per client IP or user."""

    def __init__(self, requests_per_minute: int, scope: str = "api"):
        self.requests_per_minute = requests_per_minute
        self.scope = scope
        self.window_seconds = 60

    def __call__(self, request: Request) -> None:
        settings = get_settings()
        if not settings.rate_limit_enabled:
            return

        client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or (request.client.host if request.client else "127.0.0.1")
        )
        auth_header = request.headers.get("Authorization", "")
        # Key on token fragment if available, else IP
        identifier = auth_header[-16:] if auth_header else client_ip
        key = f"idealens:ratelimit:{self.scope}:{identifier}"

        now = time.time()

        # Try Redis first
        try:
            client = build_redis_client()
            # Redis sorted set sliding window
            pipe = client.pipeline()
            pipe.zremrangebyscore(key, 0, now - self.window_seconds)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, self.window_seconds + 5)
            _, count, _, _ = pipe.execute()
            client.close()

            if count > self.requests_per_minute:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=(
                        f"Rate limit exceeded for {self.scope}. "
                        f"Limit is {self.requests_per_minute} requests per minute."
                    ),
                    headers={"Retry-After": str(self.window_seconds)},
                )
            return
        except HTTPException:
            raise
        except Exception:
            # Fall back to in-memory window
            pass

        # In-memory sliding window
        window_start = now - self.window_seconds
        timestamps = _MEM_LIMITS[key]
        _MEM_LIMITS[key] = [t for t in timestamps if t > window_start]

        if len(_MEM_LIMITS[key]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Rate limit exceeded for {self.scope}. "
                    f"Limit is {self.requests_per_minute} requests per minute."
                ),
                headers={"Retry-After": str(self.window_seconds)},
            )
        _MEM_LIMITS[key].append(now)


# Preconfigured dependencies
rate_limit_upload = RateLimiter(requests_per_minute=20, scope="uploads")
rate_limit_research = RateLimiter(requests_per_minute=15, scope="research_runs")
