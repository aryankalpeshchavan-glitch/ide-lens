"""Dependency health probes used by the /health endpoint."""

import logging

from sqlalchemy import text

from app.db import engine

logger = logging.getLogger(__name__)


def check_database_connection() -> str:
    """Probe PostgreSQL connectivity.

    Returns ``"ok"`` when a ``SELECT 1`` round-trip succeeds, otherwise
    ``"unavailable"``. The probe never raises; it is best-effort with a short
    timeout so an unreachable database cannot hang the endpoint.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return "ok"
    except Exception as exc:  # noqa: BLE001 - a probe must never raise
        logger.warning("PostgreSQL health probe failed: %s", exc)
        return "unavailable"