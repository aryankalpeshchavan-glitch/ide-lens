"""Research-run endpoints: asynchronous create, status polling, and artifacts.

Contract per ADR-0003: ``POST`` returns ``202`` with the queued run; clients
poll ``GET /{run_id}``. Artifact endpoints expose sources/evidence/analysis
records with provenance back to source identifiers.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models import (
    ClaimORM,
    CollisionCombinationORM,
    ContradictionORM,
    CoverageResultORM,
    DifferentiationRecommendationORM,
    EvidenceORM,
    GraphEdgeORM,
    GraphNodeORM,
    ReportORM,
    ResearchGapORM,
    SimilarityResultORM,
    SourceItemORM,
    StressTestResultORM,
)
from app.schemas.analysis import (
    ClaimOut,
    CollisionCombinationOut,
    ContradictionOut,
    CoverageOut,
    DifferentiationOut,
    EvidenceOut,
    GraphEdgeOut,
    GraphNodeOut,
    GraphOut,
    ReportOut,
    ResearchGapOut,
    SimilarityOut,
    SourceItemOut,
    StressTestOut,
)
from app.schemas.research import (
    ResearchRunCreate,
    ResearchRunDetail,
    ResearchRunList,
    ResearchRunSummary,
    RunEventOut,
)
from app.services.decomposition import decision_signal
from app.services.runs import (
    DIMENSIONS,
    list_runs,
    queries_for_run,
    run_counts,
)
from app.workers.dispatch import dispatch

router = APIRouter(prefix="/api/v1/research-runs", tags=["research-runs"])

_NEXT_STEPS = [
    "Lock a benchmark suite before claiming improvement.",
    "Run ablations that isolate the mechanism from alternative explanations.",
    "Verify the highest-similarity sources directly before acting.",
]


@router.post("", response_model=ResearchRunDetail, status_code=status.HTTP_202_ACCEPTED)
def create_research_run(
    request: ResearchRunCreate, session: Annotated[Session, Depends(get_session)]
) -> ResearchRunDetail:
    """Create a queued run and dispatch it (Redis worker or local executor)."""
    from app.services.runs import create_run as persist_run

    run = persist_run(
        session,
        request.idea,
        decision_signal=decision_signal(request.idea),
        source_document_id=request.document_id,
    )
    dispatch(run.id)
    session.refresh(run)
    return _to_detail(session, run)


@router.get("", response_model=ResearchRunList)
def list_research_runs(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ResearchRunList:
    """List runs, newest first, with simple paging."""
    runs = list_runs(session, limit=limit, offset=offset)
    items = [_to_summary(session, run) for run in runs]
    return ResearchRunList(items=items, total=len(items), limit=limit, offset=offset)


@router.get("/{run_id}", response_model=ResearchRunDetail)
def get_research_run(
    run_id: UUID, session: Annotated[Session, Depends(get_session)]
) -> ResearchRunDetail:
    """Fetch run metadata plus live counts, queries, and events."""
    run = _require_run(session, run_id)
    return _to_detail(session, run)


@router.get("/{run_id}/sources", response_model=list[SourceItemOut])
def get_run_sources(
    run_id: UUID, session: Annotated[Session, Depends(get_session)]
) -> list[SourceItemOut]:
    run = _require_run(session, run_id)
    rows = (
        session.query(SourceItemORM)
        .filter(
            SourceItemORM.run_id == run.id,
            SourceItemORM.dedup_status == "canonical",
        )
        .order_by(SourceItemORM.retrieved_at.desc())
        .all()
    )
    return [
        SourceItemOut(
            id=row.id,
            adapter_id=row.adapter_id,
            source_kind=row.source_kind,
            title=row.title,
            authors=row.authors or [],
            venue=row.venue,
            year=row.year,
            primary_url=row.primary_url,
            identifiers=row.identifiers or {},
            dedup_status=row.dedup_status,
            quality_signals=row.quality_signals or {},
            retrieved_at=row.retrieved_at,
        )
        for row in rows
    ]


@router.get("/{run_id}/evidence", response_model=list[EvidenceOut])
def get_run_evidence(
    run_id: UUID, session: Annotated[Session, Depends(get_session)]
) -> list[EvidenceOut]:
    run = _require_run(session, run_id)
    rows = session.query(EvidenceORM).filter(EvidenceORM.run_id == run.id).all()
    sources = {
        row.id: row
        for row in session.query(SourceItemORM).filter(SourceItemORM.run_id == run.id).all()
    }
    result = []
    for row in rows:
        source = sources.get(row.source_item_id)
        result.append(
            EvidenceOut(
                id=row.id,
                source_item_id=row.source_item_id,
                source_title=source.title if source else "",
                primary_url=source.primary_url if source else None,
                dimension=row.dimension,
                claim_text=row.claim_text,
                excerpt=row.excerpt,
                extraction_confidence=row.extraction_confidence,  # type: ignore[arg-type]
                strength=row.strength,
                created_by=row.created_by,
            )
        )
    return result


@router.get("/{run_id}/claims", response_model=list[ClaimOut])
def get_run_claims(
    run_id: UUID, session: Annotated[Session, Depends(get_session)]
) -> list[ClaimOut]:
    run = _require_run(session, run_id)
    rows = session.query(ClaimORM).filter(ClaimORM.run_id == run.id).all()
    return [ClaimOut(id=row.id, kind=row.kind, status=row.status, text=row.text) for row in rows]

@router.get("/{run_id}/similarity", response_model=list[SimilarityOut])
def get_run_similarity(
    run_id: UUID, session: Annotated[Session, Depends(get_session)]
) -> list[SimilarityOut]:
    run = _require_run(session, run_id)
    rows = (
        session.query(SimilarityResultORM)
        .filter(SimilarityResultORM.run_id == run.id)
        .order_by(SimilarityResultORM.score.desc())
        .all()
    )
    return [
        SimilarityOut(
            dimension=row.dimension,
            score=row.score,
            confidence=row.confidence,  # type: ignore[arg-type]
            explanation=row.explanation,
            evidence_ids=row.evidence_ids or [],
            lexical_score=row.lexical_score,
            structured_score=row.structured_score,
            embedding_score=row.embedding_score,
        )
        for row in rows
    ]


@router.get("/{run_id}/coverage", response_model=list[CoverageOut])
def get_run_coverage(
    run_id: UUID, session: Annotated[Session, Depends(get_session)]
) -> list[CoverageOut]:
    run = _require_run(session, run_id)
    rows = (
        session.query(CoverageResultORM)
        .filter(CoverageResultORM.run_id == run.id)
        .order_by(CoverageResultORM.dimension)
        .all()
    )
    return [
        CoverageOut(
            dimension=row.dimension,
            level=row.level,  # type: ignore[arg-type]
            explanation=row.explanation,
            evidence_count=row.evidence_count,
            source_count=row.source_count,
            confidence=row.confidence,  # type: ignore[arg-type]
        )
        for row in rows
    ]


@router.get("/{run_id}/contradictions", response_model=list[ContradictionOut])
def get_run_contradictions(
    run_id: UUID, session: Annotated[Session, Depends(get_session)]
) -> list[ContradictionOut]:
    run = _require_run(session, run_id)
    rows = session.query(ContradictionORM).filter(ContradictionORM.run_id == run.id).all()
    return [
        ContradictionOut(
            id=row.id,
            dimension=row.dimension,
            subject=row.subject,
            evidence_a_id=row.evidence_a_id,
            evidence_b_id=row.evidence_b_id,
            source_a_id=row.source_a_id,
            source_b_id=row.source_b_id,
            comparability=row.comparability,
            conflict_summary=row.conflict_summary,
            possible_explanations=row.possible_explanations or [],
            confidence=row.confidence,  # type: ignore[arg-type]
        )
        for row in rows
    ]


@router.get("/{run_id}/gaps", response_model=list[ResearchGapOut])
def get_run_gaps(
    run_id: UUID, session: Annotated[Session, Depends(get_session)]
) -> list[ResearchGapOut]:
    run = _require_run(session, run_id)
    rows = session.query(ResearchGapORM).filter(ResearchGapORM.run_id == run.id).all()
    return [
        ResearchGapOut(
            id=row.id,
            scope_kind=row.scope_kind,
            subject=row.subject or {},
            saturation_bucket=row.saturation_bucket,  # type: ignore[arg-type]
            standardized_language=row.standardized_language,
            coverage_disclosure=row.coverage_disclosure or {},
            evidence_basis=row.evidence_basis or {},
        )
        for row in rows
    ]


@router.get("/{run_id}/collisions", response_model=list[CollisionCombinationOut])
def get_run_collisions(
    run_id: UUID, session: Annotated[Session, Depends(get_session)]
) -> list[CollisionCombinationOut]:
    run = _require_run(session, run_id)
    rows = (
        session.query(CollisionCombinationORM)
        .filter(CollisionCombinationORM.run_id == run.id)
        .all()
    )
    return [
        CollisionCombinationOut(
            id=row.id,
            component_ids=row.component_ids or [],
            level=row.level,  # type: ignore[arg-type]
            evidence_count=row.evidence_count,
            explanation=row.explanation,
            confidence=row.confidence,  # type: ignore[arg-type]
        )
        for row in rows
    ]


@router.get("/{run_id}/stress-tests", response_model=list[StressTestOut])
@router.get("/{run_id}/stress-test", response_model=list[StressTestOut], include_in_schema=False)
def get_run_stress_tests(
    run_id: UUID, session: Annotated[Session, Depends(get_session)]
) -> list[StressTestOut]:
    run = _require_run(session, run_id)
    rows = session.query(StressTestResultORM).filter(StressTestResultORM.run_id == run.id).all()
    return [
        StressTestOut(
            id=row.id,
            category=row.category,
            severity=row.severity,  # type: ignore[arg-type]
            explanation=row.explanation,
            evidence_ids=row.evidence_ids or [],
            recommendation=row.recommendation,
        )
        for row in rows
    ]


@router.get("/{run_id}/differentiation", response_model=list[DifferentiationOut])
def get_run_differentiation(
    run_id: UUID, session: Annotated[Session, Depends(get_session)]
) -> list[DifferentiationOut]:
    run = _require_run(session, run_id)
    rows = (
        session.query(DifferentiationRecommendationORM)
        .filter(DifferentiationRecommendationORM.run_id == run.id)
        .all()
    )
    return [
        DifferentiationOut(
            id=row.id,
            overlap_summary=row.overlap_summary,
            overlap_evidence_ids=row.overlap_evidence_ids or [],
            differentiation_hypothesis=row.differentiation_hypothesis,
            rationale=row.rationale,
            less_represented_area=row.less_represented_area,
            supporting_evidence_ids=row.supporting_evidence_ids or [],
            remaining_uncertainty=row.remaining_uncertainty,
        )
        for row in rows
    ]


@router.get("/{run_id}/graph", response_model=GraphOut)
def get_run_graph(
    run_id: UUID, session: Annotated[Session, Depends(get_session)]
) -> GraphOut:
    run = _require_run(session, run_id)
    nodes = session.query(GraphNodeORM).filter(GraphNodeORM.run_id == run.id).all()
    edges = session.query(GraphEdgeORM).filter(GraphEdgeORM.run_id == run.id).all()
    return GraphOut(
        nodes=[
            GraphNodeOut(id=node.id, node_type=node.node_type, label=node.label)
            for node in nodes
        ],
        edges=[
            GraphEdgeOut(
                id=edge.id,
                source_node_id=edge.source_node_id,
                target_node_id=edge.target_node_id,
                relationship_type=edge.relationship_type,
                weight=edge.weight,
                confidence=edge.confidence,  # type: ignore[arg-type]
            )
            for edge in edges
        ],
    )


@router.get("/{run_id}/report", response_model=ReportOut)
def get_run_report(
    run_id: UUID, session: Annotated[Session, Depends(get_session)]
) -> ReportOut:
    run = _require_run(session, run_id)
    row = session.query(ReportORM).filter(ReportORM.run_id == run.id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Report not generated yet")
    return ReportOut(
        id=row.id,
        run_id=row.run_id,
        format=row.format,
        content=row.content,
        citations=row.citations or {},
        scope_disclosure=row.scope_disclosure or {},
        coverage=row.coverage or {},
        language_guardrail_status=row.language_guardrail_status,
        generated_at=row.generated_at,
    )

# ---------------------------------------------------------------------------
# Internal helpers (not exposed as endpoints)
# ---------------------------------------------------------------------------
def _require_run(session: Session, run_id: UUID):
    from app.services.runs import get_run as _get_run

    run = _get_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Research run not found")
    return run


def _to_summary(session: Session, run) -> ResearchRunSummary:
    canonical, evidence = run_counts(session, run)
    title = None
    if run.decomposition and isinstance(run.decomposition, dict):
        title = run.decomposition.get("title") or run.decomposition.get("objective")
    if not title:
        first_line = run.idea.split(".")[0].strip()
        title = first_line[:90] if first_line else run.idea[:90]

    return ResearchRunSummary(
        id=run.id,
        status=run.status,  # type: ignore[arg-type]
        idea=run.idea,
        title=title,
        progress=run.progress,
        current_stage=run.current_stage,
        created_at=run.created_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
        disclosure=run.disclosure,
        decision_signal=run.decision_signal or 0,
        sources_count=canonical,
        evidence_count=evidence,
    )


def _to_detail(session: Session, run) -> ResearchRunDetail:
    from app.models import RunEventORM
    from app.schemas.analysis import QueryOut

    canonical, evidence = run_counts(session, run)
    recent_events = (
        session.query(RunEventORM)
        .filter(RunEventORM.run_id == run.id)
        .order_by(RunEventORM.created_at.desc())
        .limit(25)
        .all()
    )
    events = [
        RunEventOut(
            event_type=event.event_type,
            stage=event.stage,
            payload=event.payload or {},
            created_at=event.created_at,
        )
        for event in reversed(recent_events)
    ]
    queries = [
        QueryOut(
            id=query.id,
            query_text=query.query_text,
            purpose=query.purpose,
            ordering=query.ordering,
            status=query.status,
        )
        for query in queries_for_run(session, run.id)
    ]
    return ResearchRunDetail(
        id=run.id,
        status=run.status,  # type: ignore[arg-type]
        idea=run.idea,
        progress=run.progress,
        current_stage=run.current_stage,
        created_at=run.created_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
        disclosure=run.disclosure,
        decision_signal=run.decision_signal,
        sources_count=canonical,
        evidence_count=evidence,
        source_document_id=run.source_document_id,
        decomposition=run.decomposition,
        dimensions=list(DIMENSIONS),
        next_steps=list(_NEXT_STEPS),
        error_summary=list(run.error_summary or []),
        providers=dict(run.provider_snapshot or {}),
        queries=queries,
        events=events,
    )

