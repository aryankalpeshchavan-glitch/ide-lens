"""In-process executor used when Redis is unavailable (local/dev mode).

Provide the same orchestrator entry point as the Redis worker so the API
contract is identical whether the run executes locally or on a remote worker.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

from app.db.session import SessionLocal
from app.services.orchestrator import ResearchOrchestrator
from app.sources.registry import default_registry

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="idealens-local")


def submit_local(run_id: UUID) -> None:
    """Execute a run asynchronously in this process (dev mode)."""
    orchestrator = ResearchOrchestrator(
        session_factory=SessionLocal, registry=default_registry
    )
    _executor.submit(orchestrator.execute, run_id)
    logger.info("Dispatched run %s to the local executor", run_id)