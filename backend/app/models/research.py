"""Core research entities mapped to PostgreSQL (SQLite-compatible for tests).

These models follow docs/DATA_MODEL.md. JSON columns use the generic SQLAlchemy
``JSON`` type so the same models run on PostgreSQL and SQLite.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class ResearchRunORM(Base):
    """Root record for a research run (DATA_MODEL.md §1.5)."""

    __tablename__ = "research_runs"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    idea: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    current_stage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decision_signal: Mapped[int] = mapped_column(Integer, default=0)
    disclosure: Mapped[str] = mapped_column(Text, default="")
    decomposition: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    scoring_config_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    provider_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_summary: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    source_document_id: Mapped[UUID | None] = mapped_column(
        Uuid, nullable=True, index=True
    )
    events: Mapped[list["RunEventORM"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    queries: Mapped[list["QueryORM"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    sources: Mapped[list["SourceItemORM"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    evidence: Mapped[list["EvidenceORM"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    claims: Mapped[list["ClaimORM"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    documents: Mapped[list["DocumentORM"]] = relationship(
        back_populates="run", foreign_keys="DocumentORM.run_id"
    )


class DocumentORM(Base):
    """An ingested source document (TXT, PDF, DOCX) per DATA_MODEL.md §1.3."""

    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    run_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("research_runs.id"), nullable=True, index=True
    )
    filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(128))
    size_bytes: Mapped[int] = mapped_column(Integer)
    hash_sha256: Mapped[str] = mapped_column(String(64), index=True)
    parse_status: Mapped[str] = mapped_column(String(32), default="parsed")
    extracted_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_text: Mapped[str] = mapped_column(Text)
    doc_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )

    run: Mapped[ResearchRunORM | None] = relationship(
        back_populates="documents", foreign_keys=[run_id]
    )
    chunks: Mapped[list["DocumentChunkORM"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunkORM(Base):
    """Normalized parse chunk from an ingested document per DATA_MODEL.md §1.4."""

    __tablename__ = "document_chunks"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("documents.id"), index=True
    )
    ord_index: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str] = mapped_column(Text)
    char_span: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    token_estimate: Mapped[int] = mapped_column(Integer, default=0)
    chunk_hash: Mapped[str] = mapped_column(String(64))

    document: Mapped[DocumentORM] = relationship(back_populates="chunks")


class RunEventORM(Base):
    """Append-only per-run event log (DATA_MODEL.md §2)."""

    __tablename__ = "run_events"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("research_runs.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    stage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    run: Mapped[ResearchRunORM] = relationship(back_populates="events")


class QueryORM(Base):
    """A generated retrieval query (DATA_MODEL.md §1.6)."""

    __tablename__ = "queries"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("research_runs.id"), index=True)
    query_text: Mapped[str] = mapped_column(Text)
    purpose: Mapped[str] = mapped_column(String(64))
    ordering: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(24), default="planned")

    run: Mapped[ResearchRunORM] = relationship(back_populates="queries")
class SourceItemORM(Base):
    """A single retrieved work or repository (DATA_MODEL.md §1.8)."""

    __tablename__ = "source_items"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("research_runs.id"), index=True)
    adapter_id: Mapped[str] = mapped_column(String(32), index=True)
    global_normalized_id: Mapped[str] = mapped_column(String(128), index=True)
    source_kind: Mapped[str] = mapped_column(String(24))
    identifiers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    title: Mapped[str] = mapped_column(Text)
    authors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    venue: Mapped[str | None] = mapped_column(String(255), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    abstract_or_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
    dedup_status: Mapped[str] = mapped_column(String(24), default="canonical")
    canonical_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("source_items.id"), nullable=True
    )
    quality_signals: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    fetch_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    run: Mapped[ResearchRunORM] = relationship(back_populates="sources")
    evidence: Mapped[list["EvidenceORM"]] = relationship(
        back_populates="source_item", cascade="all, delete-orphan"
    )


class EvidenceORM(Base):
    """Structured fact/passage tied to one SourceItem (EVIDENCE_MODEL.md)."""

    __tablename__ = "evidence"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("research_runs.id"), index=True)
    source_item_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("source_items.id"), index=True
    )
    dimension: Mapped[str] = mapped_column(String(40), index=True)
    claim_text: Mapped[str] = mapped_column(Text)
    excerpt: Mapped[str] = mapped_column(Text)
    excerpt_span: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    extraction_confidence: Mapped[str] = mapped_column(String(16), default="medium")
    provenance_backref: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    retrieval_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_by: Mapped[str] = mapped_column(String(64), default="deterministic")
    strength: Mapped[str] = mapped_column(String(16), default="moderate")

    run: Mapped[ResearchRunORM] = relationship(back_populates="evidence")
    source_item: Mapped[SourceItemORM] = relationship(back_populates="evidence")


class ClaimORM(Base):
    """A discrete statement the system commits to (EVIDENCE_MODEL.md §3)."""

    __tablename__ = "claims"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("research_runs.id"), index=True)
    kind: Mapped[str] = mapped_column(String(24), default="extracted_claim")
    status: Mapped[str] = mapped_column(String(24), default="grounded")
    text: Mapped[str] = mapped_column(Text)

    run: Mapped[ResearchRunORM] = relationship(back_populates="claims")
