"""Analysis, graph, and report entities (docs/DATA_MODEL.md §1.9–§1.19, §2).

All analytical outputs reference evidence ids so every conclusion resolves back
to sources (EVIDENCE_MODEL.md §6, ADR-0002).
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.research import utcnow


class SimilarityResultORM(Base):
    """Per-dimension similarity result (SCORING.md §2)."""

    __tablename__ = "similarity_results"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("research_runs.id"), index=True)
    dimension: Mapped[str] = mapped_column(String(40), index=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[str] = mapped_column(String(16), default="low")
    explanation: Mapped[str] = mapped_column(Text, default="")
    evidence_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    lexical_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    structured_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    embedding_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CoverageResultORM(Base):
    """Research coverage per idea dimension (SCORING.md §9)."""

    __tablename__ = "coverage_results"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("research_runs.id"), index=True)
    dimension: Mapped[str] = mapped_column(String(40), index=True)
    level: Mapped[str] = mapped_column(String(24))
    explanation: Mapped[str] = mapped_column(Text, default="")
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[str] = mapped_column(String(16), default="low")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContradictionORM(Base):
    """Preserved two-sided contradiction flag (SCORING.md §7)."""

    __tablename__ = "contradictions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("research_runs.id"), index=True)
    dimension: Mapped[str] = mapped_column(String(40), index=True)
    subject: Mapped[str] = mapped_column(Text, default="")
    evidence_a_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("evidence.id"), nullable=True
    )
    evidence_b_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("evidence.id"), nullable=True
    )
    source_a_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("source_items.id"), nullable=True
    )
    source_b_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("source_items.id"), nullable=True
    )
    comparability: Mapped[str] = mapped_column(String(24), default="not_checked")
    conflict_summary: Mapped[str] = mapped_column(Text, default="")
    possible_explanations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[str] = mapped_column(String(16), default="low")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ResearchGapORM(Base):
    """Evidence-based gap observation (SCORING.md §5–6)."""

    __tablename__ = "research_gaps"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("research_runs.id"), index=True)
    scope_kind: Mapped[str] = mapped_column(String(24), default="concept")
    subject: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    saturation_bucket: Mapped[str] = mapped_column(String(40))
    standardized_language: Mapped[str] = mapped_column(Text, default="")
    coverage_disclosure: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    evidence_basis: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CollisionCombinationORM(Base):
    """Idea collision combination representation (ARCHITECTURE.md M-12)."""

    __tablename__ = "collision_combinations"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("research_runs.id"), index=True)
    component_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    level: Mapped[str] = mapped_column(String(40))
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    explanation: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[str] = mapped_column(String(16), default="low")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class StressTestResultORM(Base):
    """Deterministic idea stress-test inventory (ARCHITECTURE.md M-13)."""

    __tablename__ = "stress_test_results"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("research_runs.id"), index=True)
    category: Mapped[str] = mapped_column(String(40))
    severity: Mapped[str] = mapped_column(String(16), default="medium")
    explanation: Mapped[str] = mapped_column(Text, default="")
    evidence_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    recommendation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
class DifferentiationRecommendationORM(Base):
    """Evidence-grounded differentiation direction (ARCHITECTURE.md M-14)."""

    __tablename__ = "differentiation_recommendations"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("research_runs.id"), index=True)
    overlap_summary: Mapped[str] = mapped_column(Text, default="")
    overlap_evidence_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    differentiation_hypothesis: Mapped[str] = mapped_column(Text, default="")
    rationale: Mapped[str] = mapped_column(Text, default="")
    less_represented_area: Mapped[str] = mapped_column(Text, default="")
    supporting_evidence_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    remaining_uncertainty: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ReportORM(Base):
    """Generated evidence-grounded report (DATA_MODEL.md §1.19)."""

    __tablename__ = "reports"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("research_runs.id"), unique=True, index=True
    )
    format: Mapped[str] = mapped_column(String(16), default="markdown")
    content: Mapped[str] = mapped_column(Text, default="")
    citations: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    scope_disclosure: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    coverage: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    language_guardrail_status: Mapped[str] = mapped_column(String(16), default="pending")
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class GraphNodeORM(Base):
    """Research-graph node (run-scoped) (ADR-0006)."""

    __tablename__ = "graph_nodes"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("research_runs.id"), index=True)
    node_type: Mapped[str] = mapped_column(String(32))
    label: Mapped[str] = mapped_column(Text)
    reference_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class GraphEdgeORM(Base):
    """Typed research-graph edge (ADR-0006, DATA_MODEL.md §2)."""

    __tablename__ = "graph_edges"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("research_runs.id"), index=True)
    source_node_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("graph_nodes.id"))
    target_node_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("graph_nodes.id"))
    relationship_type: Mapped[str] = mapped_column(String(40))
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[str] = mapped_column(String(16), default="low")
    provenance: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SourceProfileORM(Base):
    """Adapter/endpoint context and health (DATA_MODEL.md §1.7)."""

    __tablename__ = "source_profiles"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    adapter_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255), default="")
    provider_schema_version: Mapped[str] = mapped_column(String(32), default="1")
    credentials_configured: Mapped[bool] = mapped_column(default=False)
    last_health: Mapped[str] = mapped_column(String(16), default="unknown")
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )