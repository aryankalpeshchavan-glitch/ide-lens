"""Outbound HTTP helpers shared by source adapters.

Retries/backoff follow FAILURE_HANDLING.md §2: transient network errors and
5xx retry with exponential backoff plus jitter; HTTP 429 honors ``Retry-After``.
Non-429 4xx errors raise immediately (no automatic retry).
"""

import asyncio
import logging
import random
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_SESSION_KWARGS = ("transport",)


class TransientSourceError(RuntimeError):
    """Raised for retryable outbound failures (network, 5xx, 429)."""


class PermanentSourceError(RuntimeError):
    """Raised for non-retryable failures (auth, bad request, timeout-capped)."""


def _backoff_delay(attempt: int, base: float = 1.0, cap: float = 8.0) -> float:
    """Exponential backoff with jitter for ``attempt`` (0-based)."""
    exponential = base * (2**attempt)
    return min(cap, exponential) * (0.5 + random.random())


async def request_with_retry(
    client: httpx.AsyncClient,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    adapter_id: str = "http",
    max_retries: int | None = None,
) -> httpx.Response:
    """Perform a GET with retries; returns the final response."""
    from app.core.security import is_safe_external_url

    if not is_safe_external_url(url):
        raise PermanentSourceError(
            f"{adapter_id} blocked unsafe external URL target (SSRF guard): {url}"
        )

    settings = get_settings()
    attempts = settings.http_max_retries if max_retries is None else max_retries
    for attempt in range(attempts + 1):
        try:
            response = await client.get(url, params=params, headers=headers)
        except (httpx.TransportError, httpx.TimeoutException) as exc:
            if attempt < attempts:
                delay = _backoff_delay(attempt)
                logger.warning(
                    "%s transport error (%s); retrying in %.1fs", adapter_id, exc, delay
                )
                await asyncio.sleep(delay)
                continue
            raise TransientSourceError(str(exc)) from exc

        if response.status_code == 429:
            retry_after = _parse_retry_after(response.headers.get("Retry-After"))
            if attempt < attempts:
                delay = retry_after if retry_after is not None else _backoff_delay(attempt)
                logger.warning("%s rate-limited (429); retrying in %.1fs", adapter_id, delay)
                await asyncio.sleep(delay)
                continue
            raise TransientSourceError(f"{adapter_id} rate-limited (429)")
        if response.status_code >= 500:
            if attempt < attempts:
                delay = _backoff_delay(attempt)
                logger.warning(
                    "%s http %s; retrying in %.1fs", adapter_id, response.status_code, delay
                )
                await asyncio.sleep(delay)
                continue
            raise TransientSourceError(f"{adapter_id} http {response.status_code}")
        if response.status_code >= 400:
            raise PermanentSourceError(
                f"{adapter_id} http {response.status_code}: {response.text[:200]}"
            )
        return response
    raise TransientSourceError(f"{adapter_id} exhausted retries")


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return max(0.2, float(value))
    except ValueError:
        return None


def build_client(*, transport: Any | None = None) -> httpx.AsyncClient:
    """Build an AsyncClient configured from settings.

    ``transport`` is injected in tests (``httpx.MockTransport``) so adapters are
    exercised without any real network access.
    """
    settings = get_settings()
    kwargs: dict[str, Any] = {
        "timeout": httpx.Timeout(settings.http_timeout_seconds),
        "follow_redirects": True,
    }
    if transport is not None:
        kwargs["transport"] = transport
    return httpx.AsyncClient(**kwargs)