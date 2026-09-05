"""API schemas for research runs (asynchronous lifecycle)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.analysis import QueryOut

RunStatus = Literal["queued", "running", "completed", "partially_failed", "failed"]


class ResearchRunCreate(BaseModel):
    """Input for starting a research run."""

    idea: str = Field(min_length=20, max_length=25000)
    document_id: UUID | None = Field(default=None)


class RunEventOut(BaseModel):
    """Append-only run event surfaced to the client."""

    event_type: str
    stage: str | None = None
    payload: dict = Field(default_factory=dict)
    created_at: datetime


class ResearchRunSummary(BaseModel):
    """Stable run metadata returned by the API."""

    id: UUID
    status: RunStatus
    idea: str
    title: str | None = None
    progress: int = Field(ge=0, le=100)
    current_stage: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    disclosure: str
    decision_signal: int = 0
    sources_count: int = 0
    evidence_count: int = 0


class ResearchRunDetail(ResearchRunSummary):
    """Run metadata plus live artifact counts and disclosure."""

    decision_signal: int = Field(ge=0, le=100)
    sources_count: int = Field(ge=0)
    evidence_count: int = Field(ge=0)
    source_document_id: UUID | None = None
    decomposition: dict | None = None
    dimensions: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    error_summary: list[dict] = Field(default_factory=list)
    providers: dict = Field(default_factory=dict)
    queries: list[QueryOut] = Field(default_factory=list)
    events: list[RunEventOut] = Field(default_factory=list)


class ResearchRunList(BaseModel):
    """List response with simple paging metadata."""

    items: list[ResearchRunSummary]
    total: int = Field(ge=0)
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class ActionAccepted(BaseModel):
    """Response for a queued job (202)."""

    run_id: UUID
    status_url: str
    status: Literal["queued"]
    message: str
