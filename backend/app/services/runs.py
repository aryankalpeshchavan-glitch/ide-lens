"""Research run persistence helpers (lifecycle: queued → … → terminal)."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import (
    ClaimORM,
    EvidenceORM,
    QueryORM,
    ResearchRunORM,
    RunEventORM,
    SourceItemORM,
)

DIMENSIONS = [
    "problem",
    "objective",
    "technology",
    "method",
    "architecture",
    "dataset",
    "evaluation",
]

#: Statuses per ADR-0003 / ARCHITECTURE.md §4.
STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_PARTIALLY_FAILED = "partially_failed"
STATUS_FAILED = "failed"

TERMINAL_STATUSES = {STATUS_COMPLETED, STATUS_PARTIALLY_FAILED, STATUS_FAILED}


def create_run(
    session: Session,
    idea: str,
    *,
    decision_signal: int,
    source_document_id: UUID | None = None,
    owner_id: str | None = None,
) -> ResearchRunORM:
    """Persist a queued run with optional ownership and commit."""
    from app.models.research import DocumentORM

    now = datetime.now(UTC)
    run = ResearchRunORM(
        idea=idea.strip(),
        source_document_id=source_document_id,
        owner_id=owner_id,
        status=STATUS_QUEUED,
        progress=0,
        current_stage=None,
        decision_signal=decision_signal,
        created_at=now,
        updated_at=now,
        last_heartbeat_at=now,
        retry_count=0,
        disclosure=(
            "Scope-aware signals only: similarity never equals plagiarism, and "
            "limited evidence never proves novelty. The retrieved corpus is not "
            "the whole field; coverage is reported per dimension."
        ),
    )
    session.add(run)
    session.flush()

    if source_document_id is not None:
        doc = session.get(DocumentORM, source_document_id)
        if doc is not None:
            doc.run_id = run.id
            if owner_id and not doc.owner_id:
                doc.owner_id = owner_id

    session.commit()
    session.refresh(run)
    return run


def get_run(session: Session, run_id: UUID) -> ResearchRunORM | None:
    return session.get(ResearchRunORM, run_id)


def list_runs(
    session: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    owner_id: str | None = None,
) -> list[ResearchRunORM]:
    """List runs, optionally scoped by owner identity."""
    query = session.query(ResearchRunORM)
    if owner_id is not None:
        query = query.filter(ResearchRunORM.owner_id == owner_id)
    return (
        query.order_by(ResearchRunORM.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )


def update_heartbeat(session: Session, run: ResearchRunORM) -> None:
    """Record a liveness heartbeat timestamp for a running pipeline."""
    now = datetime.now(UTC)
    run.last_heartbeat_at = now
    run.updated_at = now


def recover_stale_runs(
    session: Session,
    *,
    timeout_seconds: int = 180,
    max_retries: int = 3,
) -> list[UUID]:
    """Detect runs stuck in running status without recent heartbeat and recover or fail them."""
    from app.workers.queue import move_to_dlq, re_enqueue_stale_job

    now = datetime.now(UTC)
    running_runs = (
        session.query(ResearchRunORM)
        .filter(ResearchRunORM.status == STATUS_RUNNING)
        .all()
    )
    recovered_ids: list[UUID] = []

    for run in running_runs:
        ref_time = run.last_heartbeat_at or run.started_at or run.updated_at
        elapsed = (now - ref_time).total_seconds() if ref_time else 9999
        if elapsed > timeout_seconds:
            recovered_ids.append(run.id)
            if run.retry_count < max_retries:
                run.retry_count += 1
                run.status = STATUS_QUEUED
                run.last_heartbeat_at = now
                add_event(
                    session,
                    run,
                    "run.recovered",
                    stage=run.current_stage,
                    payload={"retry_count": run.retry_count, "stale_seconds": elapsed},
                )
                re_enqueue_stale_job(run.id)
            else:
                run.status = STATUS_FAILED
                run.completed_at = now
                add_event(
                    session,
                    run,
                    "run.timeout_failed",
                    stage=run.current_stage,
                    payload={
                        "error": (
                            f"Run exceeded heartbeat threshold ({elapsed:.0f}s) and "
                            f"max retries ({max_retries})"
                        )
                    },
                )
                current = list(run.error_summary or [])
                current.append({
                    "class": "WORKER_TIMEOUT",
                    "stage": run.current_stage,
                    "message": (
                        f"Worker crashed or timed out after {elapsed:.0f}s without heartbeat."
                    ),
                })
                run.error_summary = current
                move_to_dlq(run.id, reason="heartbeat_timeout")

    if recovered_ids:
        session.commit()
    return recovered_ids


def run_counts(session: Session, run: ResearchRunORM) -> tuple[int, int]:
    """Return (sources_count, evidence_count) for a run."""
    canonical = session.query(SourceItemORM).filter(
        SourceItemORM.run_id == run.id,
        SourceItemORM.dedup_status == "canonical",
    ).count()
    evidence = session.query(EvidenceORM).filter(EvidenceORM.run_id == run.id).count()
    return canonical, evidence


def add_event(
    session: Session,
    run: ResearchRunORM,
    event_type: str,
    *,
    stage: str | None = None,
    payload: dict | None = None,
) -> RunEventORM:
    event = RunEventORM(
        run_id=run.id,
        event_type=event_type,
        stage=stage,
        payload=payload or {},
    )
    session.add(event)
    return event


def set_state(
    session: Session,
    run: ResearchRunORM,
    *,
    status: str | None = None,
    progress: int | None = None,
    current_stage: str | None = None,
    started: bool = False,
    completed: bool = False,
    error: dict | None = None,
) -> None:
    """Update run state fields and persist (no commit)."""
    now = datetime.now(UTC)
    if status is not None:
        run.status = status
    if progress is not None:
        run.progress = max(0, min(100, int(progress)))
    if current_stage is not None:
        run.current_stage = current_stage
    if started and run.started_at is None:
        run.started_at = now
    if completed:
        run.completed_at = now
    if error is not None:
        current = list(run.error_summary or [])
        current.append(error)
        run.error_summary = current
    run.updated_at = now


def queries_for_run(session: Session, run_id: UUID) -> list[QueryORM]:
    return (
        session.query(QueryORM)
        .filter(QueryORM.run_id == run_id)
        .order_by(QueryORM.ordering)
        .all()
    )


def claims_for_run(session: Session, run_id: UUID) -> list[ClaimORM]:
    return session.query(ClaimORM).filter(ClaimORM.run_id == run_id).all()