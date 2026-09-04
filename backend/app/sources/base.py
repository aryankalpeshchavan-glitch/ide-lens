"""Source adapter abstraction (ADR-0004).

All adapters normalize provider payloads into the canonical ``SourceItemData``
record. The retrieval orchestrator depends only on this interface: retries,
rate-limit pacing, caching, and partial-failure isolation live outside the
adapters.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SourceItemData:
    """Canonical normalized retrieval result (SOURCE_POLICY.md §7)."""

    adapter_id: str
    source_kind: str
    title: str
    identifiers: dict[str, str] = field(default_factory=dict)
    authors: list[str] = field(default_factory=list)
    venue: str | None = None
    year: int | None = None
    abstract_or_description: str | None = None
    primary_url: str | None = None
    quality_signals: dict[str, Any] = field(default_factory=dict)
    raw_payload: dict[str, Any] = field(default_factory=dict)


class SourceAdapter(ABC):
    """Interface implemented by every source adapter."""

    adapter_id: str = "base"
    display_name: str = "Base"
    provider_schema_version: str = "1"
    credentials_required: bool = False

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> list[SourceItemData]:
        """Search the provider and return canonical items."""

    @property
    def credentials_configured(self) -> bool:
        """True when the adapter has any credential it needs.

        Default behavior: an adapter that requires credentials is configured by
        default in tests; subclasses override this with real env checks.
        """
        return not self.credentials_required

    async def health_check(self) -> str:
        """Best-effort provider health probe (``ok`` / ``unavailable``)."""
        try:
            results = await self.search("attention mechanism", limit=1)
            return "ok" if results is not None else "unavailable"
        except Exception:  # noqa: BLE001 - a probe must never raise
            return "unavailable"