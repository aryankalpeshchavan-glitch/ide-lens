"""Logging configuration.

Production deployments emit structured JSON lines carrying run/stage/component
fields so log aggregation can filter per run without post-processing (see
FAILURE_HANDLING.md §9). Secrets are never logged.
"""

import json
import logging
from typing import Any


class JsonFormatter(logging.Formatter):
    """Minimal structured JSON formatter for operational logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("run_id", "stage", "component", "error_class", "retry_count", "duration_ms"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:  # noqa: N802
        return super().formatTime(record, datefmt)


def configure_logging(level: int = logging.INFO, *, json_format: bool = False) -> None:
    """Configure the root logger; ``json_format`` is enabled via settings."""
    handler = logging.StreamHandler()
    formatter = JsonFormatter() if json_format else logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)