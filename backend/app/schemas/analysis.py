"""API schemas for research-run artifacts (sources, evidence, analysis)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

CoverageLevel = Literal["strong", "moderate", "limited", "insufficient"]
Confidence = Literal["low", "medium", "high"]
SaturationBucket = Literal[
    "common", "moderately_represented", "limited_evidence_found", "insufficient_evidence"
]

#: Short alias used in artifact schemas.
Saturation = SaturationBucket


class SourceItemOut(BaseModel):
    """Canonical retrieved source item (deduplicated)."""

    id: UUID
    adapter_id: str
    source_kind: str
    title: str
    authors: list[str] = Field(default_factory=list)
    venue: str | None = None
    year: int | None = None
    primary_url: str | None = None
    identifiers: dict = Field(default_factory=dict)
    dedup_status: str = "canonical"
    quality_signals: dict = Field(default_factory=dict)
    retrieved_at: datetime


class EvidenceOut(BaseModel):
    """Structured evidence with provenance back-reference."""

    id: UUID
    source_item_id: UUID
    source_title: str = ""
    primary_url: str | None = None
    dimension: str
    claim_text: str
    excerpt: str
    extraction_confidence: Confidence
    strength: str
    created_by: str


class ClaimOut(BaseModel):
    id: UUID
    kind: str
    status: str
    text: str


class SimilarityOut(BaseModel):
    dimension: str
    score: float = Field(ge=0, le=1)
    confidence: Confidence
    explanation: str
    evidence_ids: list[UUID] = Field(default_factory=list)
    lexical_score: float | None = None
    structured_score: float | None = None
    embedding_score: float | None = None


class CoverageOut(BaseModel):
    dimension: str
    level: CoverageLevel
    explanation: str
    evidence_count: int
    source_count: int
    confidence: Confidence


class ContradictionOut(BaseModel):
    id: UUID
    dimension: str
    subject: str
    evidence_a_id: UUID | None = None
    evidence_b_id: UUID | None = None
    source_a_id: UUID | None = None
    source_b_id: UUID | None = None
    comparability: str
    conflict_summary: str
    possible_explanations: list[str] = Field(default_factory=list)
    confidence: Confidence


class ResearchGapOut(BaseModel):
    id: UUID
    scope_kind: str
    subject: dict = Field(default_factory=dict)
    saturation_bucket: Saturation
    standardized_language: str
    coverage_disclosure: dict = Field(default_factory=dict)
    evidence_basis: dict = Field(default_factory=dict)


class CollisionCombinationOut(BaseModel):
    id: UUID
    component_ids: list[str] = Field(default_factory=list)
    level: Saturation
    evidence_count: int
    explanation: str
    confidence: Confidence


class StressTestOut(BaseModel):
    id: UUID
    category: str
    severity: Literal["low", "medium", "high", "critical"]
    explanation: str
    evidence_ids: list[UUID] = Field(default_factory=list)
    recommendation: str = ""


class DifferentiationOut(BaseModel):
    id: UUID
    overlap_summary: str
    overlap_evidence_ids: list[UUID] = Field(default_factory=list)
    differentiation_hypothesis: str
    rationale: str
    less_represented_area: str
    supporting_evidence_ids: list[UUID] = Field(default_factory=list)
    remaining_uncertainty: str


class GraphNodeOut(BaseModel):
    id: UUID
    node_type: str
    label: str


class GraphEdgeOut(BaseModel):
    id: UUID
    source_node_id: UUID
    target_node_id: UUID
    relationship_type: str
    weight: float | None = None
    confidence: Confidence


class GraphOut(BaseModel):
    nodes: list[GraphNodeOut] = Field(default_factory=list)
    edges: list[GraphEdgeOut] = Field(default_factory=list)


class ReportOut(BaseModel):
    id: UUID
    run_id: UUID
    format: str
    content: str
    citations: dict = Field(default_factory=dict)
    scope_disclosure: dict = Field(default_factory=dict)
    coverage: dict = Field(default_factory=dict)
    language_guardrail_status: str
    generated_at: datetime


class QueryOut(BaseModel):
    id: UUID
    query_text: str
    purpose: str
    ordering: int
    status: str