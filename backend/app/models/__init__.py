"""Domain models mapped in M2 (DATA_MODEL.md entities).

Entities follow the M0 entity-discipline principle: each carries a clear domain
responsibility or traceability need. Duplicates are linked (canonical_id), never
silently dropped; every analytical output references evidence/source ids.
"""

from app.db.base import Base
from app.models.analysis import (
    CollisionCombinationORM,
    ContradictionORM,
    CoverageResultORM,
    DifferentiationRecommendationORM,
    GraphEdgeORM,
    GraphNodeORM,
    ReportORM,
    ResearchGapORM,
    SimilarityResultORM,
    SourceProfileORM,
    StressTestResultORM,
)
from app.models.research import (
    ClaimORM,
    DocumentChunkORM,
    DocumentORM,
    EvidenceORM,
    QueryORM,
    ResearchRunORM,
    RunEventORM,
    SourceItemORM,
)

__all__ = [
    "Base",
    "ClaimORM",
    "CollisionCombinationORM",
    "ContradictionORM",
    "CoverageResultORM",
    "DifferentiationRecommendationORM",
    "DocumentChunkORM",
    "DocumentORM",
    "EvidenceORM",
    "GraphEdgeORM",
    "GraphNodeORM",
    "QueryORM",
    "ReportORM",
    "ResearchGapORM",
    "ResearchRunORM",
    "RunEventORM",
    "SimilarityResultORM",
    "SourceItemORM",
    "SourceProfileORM",
    "StressTestResultORM",
]