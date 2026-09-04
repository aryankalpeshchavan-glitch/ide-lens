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
) -> ResearchRunORM:
    """Persist a queued run and commit."""
    from app.models.research import DocumentORM

    now = datetime.now(UTC)
    run = ResearchRunORM(
        idea=idea.strip(),
        source_document_id=source_document_id,
        status=STATUS_QUEUED,
        progress=0,
        current_stage=None,
        decision_signal=decision_signal,
        created_at=now,
        updated_at=now,
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

    session.commit()
    session.refresh(run)
    return run


def get_run(session: Session, run_id: UUID) -> ResearchRunORM | None:
    return session.get(ResearchRunORM, run_id)


def list_runs(
    session: Session, *, limit: int = 50, offset: int = 0
) -> list[ResearchRunORM]:
    return (
        session.query(ResearchRunORM)
        .order_by(ResearchRunORM.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )


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