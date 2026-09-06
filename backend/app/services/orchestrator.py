"""Research orchestration: the staged pipeline (ARCHITECTURE.md §3).

Each stage persists its artifacts and updates run state before proceeding
(stage checkpointing, FAILURE_HANDLING.md §8). A failed stage is recorded and
later stages that can still proceed do so; the run finishes ``completed`` or
``partially_failed`` with explicit disclosure.
"""

import asyncio
import logging
from uuid import UUID

from app.analysis.coverage import compute_coverage
from app.core.config import get_settings
from app.models import (
    QueryORM,
    SourceItemORM,
)
from app.services.decomposition import decompose
from app.services.normalization import fingerprint_group, normalize_source_item
from app.services.query_planning import plan_queries
from app.services.retrieval import run_retrieval
from app.services.runs import (
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_PARTIALLY_FAILED,
    STATUS_RUNNING,
    add_event,
    get_run,
    queries_for_run,
    recover_stale_runs,
    set_state,
    update_heartbeat,
)
from app.sources.registry import AdapterRegistry, default_registry

logger = logging.getLogger(__name__)

#: Stage order and per-stage progress points (checkpointable sequence).
STAGES = [
    ("decomposition", 5),
    ("query_generation", 10),
    ("retrieval", 35),
    ("normalization", 45),
    ("evidence_extraction", 55),
    ("similarity_analysis", 65),
    ("coverage_analysis", 70),
    ("contradiction_analysis", 75),
    ("gap_analysis", 80),
    ("collision_analysis", 84),
    ("stress_testing", 88),
    ("differentiation", 92),
    ("graph_construction", 95),
    ("report_generation", 99),
]

_STAGE_PROGRESS = dict(STAGES)


class ResearchOrchestrator:
    """Executes the full research-run pipeline for one run id."""

    def __init__(
        self,
        session_factory,
        registry: AdapterRegistry | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._registry = registry or default_registry

    def recover_stale(self) -> list[UUID]:
        """Trigger stale run recovery using current settings."""
        settings = get_settings()
        with self._session_factory() as session:
            return recover_stale_runs(
                session,
                timeout_seconds=settings.worker_stale_run_timeout_seconds,
                max_retries=settings.worker_max_retries,
            )

    def execute(self, run_id: UUID) -> str:
        """Run all stages; returns the final status."""
        observed_errors: list[dict] = []
        with self._session_factory() as session:
            run = get_run(session, run_id)
            if run is None:
                return STATUS_FAILED
            update_heartbeat(session, run)
            set_state(
                session, run, status=STATUS_RUNNING, progress=2,
                current_stage="decomposition", started=True,
            )
            add_event(session, run, "run.started")
            session.commit()

        for stage_name, _progress in STAGES:
            self._run_stage(run_id, stage_name, observed_errors)

        with self._session_factory() as session:
            run = get_run(session, run_id)
            if run is None:
                return STATUS_FAILED
            status = STATUS_PARTIALLY_FAILED if observed_errors else STATUS_COMPLETED
            update_heartbeat(session, run)
            set_state(
                session, run, status=status, progress=100, current_stage=None,
                completed=True,
            )
            for error in observed_errors:
                current = list(run.error_summary or [])
                if error not in current:
                    current.append(error)
                run.error_summary = current
            add_event(
                session, run,
                "run.completed" if status == STATUS_COMPLETED else "run.partially_failed",
                payload={"errors": len(observed_errors)},
            )
            session.commit()
        logger.info("Run %s finished with status %s", run_id, status)
        return status

    # ------------------------------------------------------------------ utils
    def _run_stage(
        self, run_id: UUID, stage_name: str, observed_errors: list[dict]
    ) -> None:
        """Run one stage with checkpointing; failures are isolated."""
        with self._session_factory() as session:
            run = get_run(session, run_id)
            if run is None:
                return
            update_heartbeat(session, run)
            set_state(session, run, current_stage=stage_name)
            add_event(session, run, "stage.started", stage=stage_name)
            session.commit()
        try:
            self._stage(stage_name, run_id)
            with self._session_factory() as session:
                run = get_run(session, run_id)
                if run:
                    update_heartbeat(session, run)
                    set_state(
                        session, run,
                        progress=_STAGE_PROGRESS.get(stage_name, run.progress),
                    )
                    add_event(session, run, "stage.completed", stage=stage_name)
                    session.commit()
        except Exception as exc:  # noqa: BLE001 - stage isolation boundary
            logger.warning("Stage %s failed for run %s: %s", stage_name, run_id, exc)
            observed_errors.append(
                {"class": "STAGE_ERROR", "stage": stage_name, "message": str(exc)[:300]}
            )
            with self._session_factory() as session:
                run = get_run(session, run_id)
                add_event(
                    session, run, "stage.failed", stage=stage_name,
                    payload={"error": str(exc)[:300]},
                )
                session.commit()

    def _stage(self, stage_name: str, run_id: UUID) -> None:
        if stage_name == "decomposition":
            self._stage_decomposition(run_id)
        elif stage_name == "query_generation":
            self._stage_query_planning(run_id)
        elif stage_name == "retrieval":
            asyncio.run(self._stage_retrieval(run_id))
        elif stage_name == "normalization":
            self._stage_normalization(run_id)
        elif stage_name == "evidence_extraction":
            self._stage_evidence(run_id)
        elif stage_name == "similarity_analysis":
            self._stage_similarity(run_id)
        elif stage_name == "coverage_analysis":
            self._stage_coverage(run_id)
        elif stage_name == "contradiction_analysis":
            self._stage_contradictions(run_id)
        elif stage_name == "gap_analysis":
            self._stage_gaps(run_id)
        elif stage_name == "collision_analysis":
            self._stage_collisions(run_id)
        elif stage_name == "stress_testing":
            self._stage_stress(run_id)
        elif stage_name == "differentiation":
            self._stage_differentiation(run_id)
        elif stage_name == "graph_construction":
            self._stage_graph(run_id)
        elif stage_name == "report_generation":
            self._stage_report(run_id)

    # --------------------------------------------------------------- stages A-B
    def _stage_decomposition(self, run_id: UUID) -> None:
        settings = get_settings()
        with self._session_factory() as session:
            run = get_run(session, run_id)
            run.decomposition = decompose(run.idea)
            run.provider_snapshot = {
                "ai_provider": settings.ai_provider,
                "embedding_provider": settings.embedding_provider,
            }
            run.scoring_config_snapshot = {
                "dimensions": [
                    "problem", "objective", "technology", "method",
                    "architecture", "dataset", "evaluation",
                ],
                "bands": {
                    "very_high": 0.8, "high": 0.6, "moderate": 0.4,
                    "low": 0.2, "very_low": 0.0,
                },
                "excerpt_char_limit": settings.excerpt_char_limit,
            }
            session.commit()

    def _stage_query_planning(self, run_id: UUID) -> None:
        with self._session_factory() as session:
            run = get_run(session, run_id)
            for query in plan_queries(run.idea):
                session.add(
                    QueryORM(
                        run_id=run.id,
                        query_text=query["query_text"],
                        purpose=query["purpose"],
                        ordering=query["ordering"],
                    )
                )
            session.commit()

    # ------------------------------------------------------------------ stage C
    async def _stage_retrieval(self, run_id: UUID) -> None:
        settings = get_settings()
        with self._session_factory() as session:
            run = get_run(session, run_id)
            queries = [
                {"id": q.id, "query_text": q.query_text} for q in queries_for_run(session, run.id)
            ]
        if not queries or not self._registry.all():
            return

        semaphore = asyncio.Semaphore(settings.retrieval_max_concurrency)
        items, failures = await run_retrieval(
            self._registry,
            queries,
            limit=settings.retrieval_limit_per_source,
            semaphore=semaphore,
            idea=run.idea,
        )

        with self._session_factory() as session:
            run = get_run(session, run_id)
            for query in queries:
                row = session.get(QueryORM, query["id"])
                row.status = "executed"
            for item in items:
                fields = normalize_source_item(item.adapter_id, item)
                session.add(
                    SourceItemORM(
                        run_id=run.id,
                        retrieved_at=run.created_at,
                        fetch_metadata={"cache_hit": False},
                        **fields,
                    )
                )
            for failure in failures:
                add_event(
                    session, run, "source.failed", stage="retrieval",
                    payload={
                        "adapter_id": failure["adapter_id"],
                        "query": failure["query"][:100],
                        "error": failure["error"][:300],
                        "error_class": failure["class"],
                    },
                )
            session.commit()
    # --------------------------------------------------------------- stages D-E
    def _stage_normalization(self, run_id: UUID) -> None:
        """Link duplicates; duplicates are never dropped (DATA_MODEL.md §4)."""
        with self._session_factory() as session:
            items = (
                session.query(SourceItemORM)
                .filter(SourceItemORM.run_id == run_id)
                .order_by(SourceItemORM.retrieved_at.asc(), SourceItemORM.id.asc())
                .all()
            )
            groups: dict[str, UUID] = {}
            for item in items:
                key = fingerprint_group(
                    {
                        "identifiers": item.identifiers or {},
                        "title": item.title,
                        "abstract_or_description": item.abstract_or_description,
                    }
                )
                if key in groups:
                    item.dedup_status = "duplicate_of"
                    item.canonical_id = groups[key]
                else:
                    groups[key] = item.id
            session.commit()

    def _stage_evidence(self, run_id: UUID) -> None:
        from app.evidence.extraction import extract_evidence
        from app.models import ClaimORM, EvidenceORM

        with self._session_factory() as session:
            run = get_run(session, run_id)
            rows = (
                session.query(SourceItemORM)
                .filter(
                    SourceItemORM.run_id == run.id,
                    SourceItemORM.dedup_status == "canonical",
                )
                .all()
            )
            sources = [
                {
                    "id": row.id,
                    "title": row.title,
                    "abstract_or_description": row.abstract_or_description,
                    "identifiers": row.identifiers or {},
                    "primary_url": row.primary_url,
                    "year": row.year,
                    "quality_signals": row.quality_signals or {},
                }
                for row in rows
            ]
            records = extract_evidence(sources, run.decomposition or {})
            for record in records:
                session.add(EvidenceORM(run_id=run.id, **record))
                session.add(
                    ClaimORM(
                        run_id=run.id,
                        kind="extracted_claim",
                        status="grounded",
                        text=record["claim_text"],
                    )
                )
            session.commit()

    # --------------------------------------------------------------- stages F-G
    def _stage_similarity(self, run_id: UUID) -> None:
        from app.analysis.similarity import compute_similarity
        from app.models import EvidenceORM, SimilarityResultORM

        with self._session_factory() as session:
            run = get_run(session, run_id)
            rows = session.query(EvidenceORM).filter(EvidenceORM.run_id == run.id).all()
            evidences = [
                {
                    "id": row.id,
                    "dimension": row.dimension,
                    "excerpt": row.excerpt,
                    "claim_text": row.claim_text,
                }
                for row in rows
            ]
            records = compute_similarity(run.decomposition or {}, evidences)
            for record in records:
                session.add(
                    SimilarityResultORM(
                        run_id=run.id,
                        dimension=record["dimension"],
                        score=record["score"],
                        confidence=record["confidence"],
                        explanation=record["explanation"],
                        evidence_ids=record["evidence_ids"],
                        lexical_score=record["lexical_score"],
                        structured_score=record["structured_score"],
                        embedding_score=record["embedding_score"],
                    )
                )
            session.commit()

    def _stage_coverage(self, run_id: UUID) -> None:
        from app.models import CoverageResultORM, EvidenceORM, SourceItemORM

        with self._session_factory() as session:
            run = get_run(session, run_id)
            rows = session.query(EvidenceORM).filter(EvidenceORM.run_id == run.id).all()
            sources = session.query(SourceItemORM).filter(SourceItemORM.run_id == run.id).all()
            source_ids = {str(row.source_item_id) for row in rows}
            source_adapter_counts = {
                str(row.id): row.adapter_id for row in sources if str(row.id) in source_ids
            }
            evidences = [
                {
                    "id": row.id,
                    "dimension": row.dimension,
                    "source_item_id": row.source_item_id,
                    "adapter_id": source_adapter_counts.get(str(row.source_item_id)),
                    "strength": row.strength,
                }
                for row in rows
            ]
            records = compute_coverage(evidences, source_adapter_counts)
            for record in records:
                session.add(
                    CoverageResultORM(
                        run_id=run.id,
                        dimension=record["dimension"],
                        level=record["level"],
                        explanation=record["explanation"],
                        evidence_count=record["evidence_count"],
                        source_count=record["source_count"],
                        confidence=record["confidence"],
                    )
                )
            session.commit()

    # ------------------------------------------------------------- stages H-M
    def _stage_contradictions(self, run_id: UUID) -> None:
        from app.analysis.contradictions import compute_contradictions
        from app.models import ContradictionORM, EvidenceORM, SourceItemORM

        with self._session_factory() as session:
            run = get_run(session, run_id)
            rows = session.query(EvidenceORM).filter(EvidenceORM.run_id == run.id).all()
            sources = {
                str(row.id): {"venue": row.venue}
                for row in session.query(SourceItemORM).filter(SourceItemORM.run_id == run.id).all()
            }
            evidences = [
                {
                    "id": row.id,
                    "source_item_id": row.source_item_id,
                    "dimension": row.dimension,
                    "excerpt": row.excerpt,
                    "claim_text": row.claim_text,
                }
                for row in rows
            ]
            records = compute_contradictions(evidences, sources)
            for record in records:
                session.add(
                    ContradictionORM(
                        run_id=run.id,
                        dimension=record["dimension"],
                        subject=record["subject"],
                        evidence_a_id=record["evidence_a_id"],
                        evidence_b_id=record["evidence_b_id"],
                        source_a_id=record["source_a_id"],
                        source_b_id=record["source_b_id"],
                        comparability=record["comparability"],
                        conflict_summary=record["conflict_summary"],
                        possible_explanations=record["possible_explanations"],
                        confidence=record["confidence"],
                    )
                )
            session.commit()

    def _stage_gaps(self, run_id: UUID) -> None:
        from app.analysis.gaps import compute_gaps
        from app.models import CoverageResultORM, EvidenceORM, ResearchGapORM

        with self._session_factory() as session:
            run = get_run(session, run_id)
            evidences = [
                {
                    "id": row.id,
                    "dimension": row.dimension,
                    "excerpt": row.excerpt,
                    "claim_text": row.claim_text,
                }
                for row in session.query(EvidenceORM).filter(EvidenceORM.run_id == run.id).all()
            ]
            coverage = [
                {
                    "dimension": row.dimension,
                    "level": row.level,
                    "evidence_count": row.evidence_count,
                }
                for row in session.query(CoverageResultORM)
                .filter(CoverageResultORM.run_id == run.id)
                .all()
            ]
            queries = queries_for_run(session, run.id)
            planned = max(1, len(queries))
            executed = sum(1 for q in queries if q.status == "executed")
            records = compute_gaps(
                run.decomposition or {}, evidences, coverage,
                queries_planned=planned, queries_executed=executed,
            )
            for record in records:
                session.add(ResearchGapORM(run_id=run.id, **record))
            session.commit()
    def _stage_collisions(self, run_id: UUID) -> None:
        from app.analysis.collisions import compute_collisions
        from app.models import CollisionCombinationORM, EvidenceORM

        with self._session_factory() as session:
            run = get_run(session, run_id)
            evidences = [
                {
                    "id": row.id,
                    "excerpt": row.excerpt,
                    "claim_text": row.claim_text,
                }
                for row in session.query(EvidenceORM).filter(EvidenceORM.run_id == run.id).all()
            ]
            records = compute_collisions(run.decomposition or {}, evidences)
            for record in records:
                session.add(
                    CollisionCombinationORM(
                        run_id=run.id,
                        component_ids=record["component_ids"],
                        level=record["level"],
                        evidence_count=record["evidence_count"],
                        explanation=record["explanation"],
                        confidence=record["confidence"],
                    )
                )
            session.commit()

    def _stage_stress(self, run_id: UUID) -> None:
        from app.analysis.stress import compute_stress
        from app.models import (
            CoverageResultORM,
            EvidenceORM,
            SimilarityResultORM,
            StressTestResultORM,
        )

        with self._session_factory() as session:
            run = get_run(session, run_id)
            similarity = [
                {
                    "dimension": row.dimension,
                    "score": row.score,
                    "confidence": row.confidence,
                    "evidence_ids": row.evidence_ids or [],
                }
                for row in session.query(SimilarityResultORM).filter(
                    SimilarityResultORM.run_id == run.id
                ).all()
            ]
            coverage = [
                {"dimension": row.dimension, "level": row.level}
                for row in session.query(CoverageResultORM).filter(
                    CoverageResultORM.run_id == run.id
                ).all()
            ]
            evidence_count = session.query(EvidenceORM).filter(
                EvidenceORM.run_id == run.id
            ).count()
            records = compute_stress(
                run.idea, similarity, coverage, evidence_count=evidence_count
            )
            for record in records:
                session.add(
                    StressTestResultORM(
                        run_id=run.id,
                        category=record["category"],
                        severity=record["severity"],
                        explanation=record["explanation"],
                        evidence_ids=record["evidence_ids"],
                        recommendation=record["recommendation"],
                    )
                )
            session.commit()
    def _stage_differentiation(self, run_id: UUID) -> None:
        from app.analysis.differentiation import compute_differentiation
        from app.models import (
            CollisionCombinationORM,
            DifferentiationRecommendationORM,
            ResearchGapORM,
            SimilarityResultORM,
        )

        with self._session_factory() as session:
            run = get_run(session, run_id)
            similarity = [
                {
                    "dimension": row.dimension,
                    "score": row.score,
                    "confidence": row.confidence,
                    "evidence_ids": row.evidence_ids or [],
                }
                for row in session.query(SimilarityResultORM).filter(
                    SimilarityResultORM.run_id == run.id
                ).all()
            ]
            gaps = [
                {
                    "scope_kind": row.scope_kind,
                    "subject": row.subject or {},
                    "saturation_bucket": row.saturation_bucket,
                    "evidence_basis": row.evidence_basis or {},
                }
                for row in session.query(ResearchGapORM).filter(
                    ResearchGapORM.run_id == run.id
                ).all()
            ]
            collisions = [
                {"component_ids": row.component_ids or [], "level": row.level}
                for row in session.query(CollisionCombinationORM).filter(
                    CollisionCombinationORM.run_id == run.id
                ).all()
            ]
            records = compute_differentiation(similarity, gaps, collisions)
            for record in records:
                session.add(DifferentiationRecommendationORM(run_id=run.id, **record))
            session.commit()

    # --------------------------------------------------------------- stage N
    def _stage_graph(self, run_id: UUID) -> None:
        from app.graph.builder import build_graph
        from app.models import (
            CoverageResultORM,
            EvidenceORM,
            GraphEdgeORM,
            GraphNodeORM,
            SourceItemORM,
        )

        with self._session_factory() as session:
            run = get_run(session, run_id)
            sources = [
                {"id": row.id, "title": row.title}
                for row in session.query(SourceItemORM)
                .filter(
                    SourceItemORM.run_id == run.id,
                    SourceItemORM.dedup_status == "canonical",
                )
                .all()
            ]
            evidences = [
                {
                    "id": row.id,
                    "source_item_id": row.source_item_id,
                    "dimension": row.dimension,
                    "strength": row.strength,
                    "extraction_confidence": row.extraction_confidence,
                }
                for row in session.query(EvidenceORM).filter(
                    EvidenceORM.run_id == run.id
                ).all()
            ]
            coverage = [
                row.dimension
                for row in session.query(CoverageResultORM).filter(
                    CoverageResultORM.run_id == run.id
                ).all()
            ]
            dimensions = list(dict.fromkeys(coverage))
            nodes, edges = build_graph(
                idea=run.idea, sources=sources, evidences=evidences, dimensions=dimensions
            )

            key_to_id: dict[str, UUID] = {}
            for node in nodes:
                row = GraphNodeORM(
                    run_id=run.id,
                    node_type=node["node_type"],
                    label=node["label"],
                    reference_id=node.get("reference_id"),
                )
                session.add(row)
                session.flush()
                key_to_id[node["id"]] = row.id
            for edge in edges:
                source_id = key_to_id.get(edge["source_node_id"])
                target_id = key_to_id.get(edge["target_node_id"])
                if source_id is None or target_id is None:
                    continue
                session.add(
                    GraphEdgeORM(
                        run_id=run.id,
                        source_node_id=source_id,
                        target_node_id=target_id,
                        relationship_type=edge["relationship_type"],
                        weight=edge.get("weight"),
                        confidence=edge.get("confidence", "low"),
                    )
                )
            session.commit()
    def _stage_report(self, run_id: UUID) -> None:
        from app.models import (
            CollisionCombinationORM,
            ContradictionORM,
            CoverageResultORM,
            DifferentiationRecommendationORM,
            EvidenceORM,
            ReportORM,
            ResearchGapORM,
            SimilarityResultORM,
            SourceItemORM,
            StressTestResultORM,
        )
        from app.reports.generator import check_language, render_report

        with self._session_factory() as session:
            run = get_run(session, run_id)
            sources = [
                {
                    "id": row.id,
                    "title": row.title,
                    "primary_url": row.primary_url,
                    "identifiers": row.identifiers or {},
                }
                for row in session.query(SourceItemORM)
                .filter(
                    SourceItemORM.run_id == run.id,
                    SourceItemORM.dedup_status == "canonical",
                )
                .all()
            ]
            evidences = [
                {
                    "id": row.id,
                    "source_item_id": row.source_item_id,
                    "dimension": row.dimension,
                    "excerpt": row.excerpt,
                }
                for row in session.query(EvidenceORM).filter(
                    EvidenceORM.run_id == run.id
                ).all()
            ]
            similarity = [
                {
                    "dimension": row.dimension,
                    "score": row.score,
                    "confidence": row.confidence,
                    "explanation": row.explanation,
                    "evidence_ids": row.evidence_ids or [],
                }
                for row in session.query(SimilarityResultORM).filter(
                    SimilarityResultORM.run_id == run.id
                ).all()
            ]
            coverage = [
                {
                    "dimension": row.dimension,
                    "level": row.level,
                    "evidence_count": row.evidence_count,
                    "source_count": row.source_count,
                    "explanation": row.explanation,
                }
                for row in session.query(CoverageResultORM).filter(
                    CoverageResultORM.run_id == run.id
                ).all()
            ]
            contradictions = [
                {
                    "subject": row.subject,
                    "conflict_summary": row.conflict_summary,
                    "comparability": row.comparability,
                }
                for row in session.query(ContradictionORM).filter(
                    ContradictionORM.run_id == run.id
                ).all()
            ]
            gaps = [
                {
                    "saturation_bucket": row.saturation_bucket,
                    "standardized_language": row.standardized_language,
                }
                for row in session.query(ResearchGapORM).filter(
                    ResearchGapORM.run_id == run.id
                ).all()
            ]
            collisions = [
                {
                    "component_ids": row.component_ids or [],
                    "level": row.level,
                    "evidence_count": row.evidence_count,
                }
                for row in session.query(CollisionCombinationORM).filter(
                    CollisionCombinationORM.run_id == run.id
                ).all()
            ]
            stress = [
                {"category": row.category, "severity": row.severity, "explanation": row.explanation}
                for row in session.query(StressTestResultORM).filter(
                    StressTestResultORM.run_id == run.id
                ).all()
            ]
            differentiations = [
                {
                    "overlap_summary": row.overlap_summary,
                    "less_represented_area": row.less_represented_area,
                    "remaining_uncertainty": row.remaining_uncertainty,
                }
                for row in session.query(DifferentiationRecommendationORM).filter(
                    DifferentiationRecommendationORM.run_id == run.id
                ).all()
            ]
            queries = [{"query_text": q.query_text} for q in queries_for_run(session, run.id)]
            executed_count = sum(
                1 for q in queries_for_run(session, run.id) if q.status == "executed"
            )
            failed_events = [e for e in run.events if e.event_type == "source.failed"]

            report_text, citations = render_report(
                idea=run.idea,
                sources=sources,
                evidences=evidences,
                similarity_results=similarity,
                coverage_results=coverage,
                contradictions=contradictions,
                gaps=gaps,
                collisions=collisions,
                stress_tests=stress,
                differentiations=differentiations,
                queries=queries,
                disclosure={
                    "queries_planned": len(queries),
                    "queries_executed": executed_count,
                    "retrieval_errors": len(failed_events),
                    "cache_served_items": 0,
                },
            )
            guardrail_status = "passed" if not check_language(report_text) else "failed"
            session.add(
                ReportORM(
                    run_id=run.id,
                    format="markdown",
                    content=report_text,
                    citations={"items": citations},
                    scope_disclosure={
                        "queries_planned": len(queries),
                        "queries_executed": executed_count,
                        "retrieval_errors": len(failed_events),
                        "cache_served_items": 0,
                    },
                    coverage={"dimensions": coverage},
                    language_guardrail_status=guardrail_status,
                )
            )
            session.commit()
