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
from app.workers.queue import dequeue_run


def main() -> None:
    configure_logging()
    logger = logging.getLogger("idealens.worker")
    orchestrator = ResearchOrchestrator(
        session_factory=SessionLocal, registry=default_registry
    )
    logger.info("IdeaLens worker started; waiting for jobs on Redis.")
    while True:
        run_id = dequeue_run()
        if run_id is None:
            continue
        logger.info("Claimed run %s", run_id)
        orchestrator.execute(UUID(run_id))


if __name__ == "__main__":
    main()