"""Background worker CLI (ADR-0003).

Consumes the Redis research queue and executes the staged pipeline.

Usage::

    python -m app.workers.runner

Run the API and one or more worker instances for the production execution path.
When Redis is not running locally, the API falls back to the in-process
executor and no worker is required.
"""

import logging
from uuid import UUID

from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.services.orchestrator import ResearchOrchestrator
from app.sources.registry import default_registry
from app.workers.queue import ack_run, dequeue_run


def main() -> None:
    configure_logging()
    logger = logging.getLogger("idealens.worker")
    orchestrator = ResearchOrchestrator(
        session_factory=SessionLocal, registry=default_registry
    )
    logger.info("IdeaLens worker started; waiting for jobs on Redis.")
    while True:
        try:
            # Check for crashed/stale runs periodically when worker checks queue
            orchestrator.recover_stale()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Error checking stale runs: %s", exc)

        run_id = dequeue_run()
        if run_id is None:
            continue
        logger.info("Claimed run %s", run_id)
        try:
            orchestrator.execute(UUID(run_id))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Uncaught exception while executing run %s: %s", run_id, exc)
        finally:
            # Acknowledge and remove from processing queue
            ack_run(run_id)


if __name__ == "__main__":
    main()