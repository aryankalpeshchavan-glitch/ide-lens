"""Run dispatch: Redis queue first, local executor as fallback (ADR-0003).

Tests set ``RUN_SYNC_EXECUTION=true`` (or patch this module) so runs execute
deterministically in-process without a worker or external infrastructure.
"""

from uuid import UUID

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.orchestrator import ResearchOrchestrator
from app.workers.local import submit_local
from app.workers.queue import enqueue_run


def dispatch(run_id: UUID) -> str:
    """Dispatch a run to Redis, the local executor, or (in tests) synchronously."""
    settings = get_settings()
    if settings.run_sync_execution:
        orchestrator = ResearchOrchestrator(session_factory=SessionLocal)
        orchestrator.execute(run_id)
        return "sync"
    if enqueue_run(run_id):
        return "redis"
    submit_local(run_id)
    return "local"