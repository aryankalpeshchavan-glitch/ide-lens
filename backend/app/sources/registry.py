"""Adapter registry: builds the configured source adapters."""

from app.core.config import get_settings
from app.sources.arxiv import ArxivAdapter
from app.sources.base import SourceAdapter
from app.sources.crossref import CrossrefAdapter
from app.sources.github import GithubAdapter
from app.sources.semantic_scholar import SemanticScholarAdapter

_ADAPTER_FACTORIES: dict[str, type[SourceAdapter]] = {
    "semantic_scholar": SemanticScholarAdapter,
    "crossref": CrossrefAdapter,
    "arxiv": ArxivAdapter,
    "github": GithubAdapter,
}


class AdapterRegistry:
    """Instantiate adapters from the enabled set and look them up by id."""

    def __init__(self, enabled_ids: list[str] | None = None) -> None:
        enabled = enabled_ids
        if enabled is None:
            settings = get_settings()
            enabled = [
                item.strip()
                for item in settings.enabled_adapters.split(",")
                if item.strip()
            ]
        self._adapters: dict[str, SourceAdapter] = {}
        for adapter_id in enabled:
            factory = _ADAPTER_FACTORIES.get(adapter_id)
            if factory is not None:
                self._adapters[adapter_id] = factory()

    def get(self, adapter_id: str) -> SourceAdapter | None:
        return self._adapters.get(adapter_id)

    def all(self) -> list[SourceAdapter]:
        return list(self._adapters.values())

    def ids(self) -> list[str]:
        return list(self._adapters.keys())


default_registry = AdapterRegistry()