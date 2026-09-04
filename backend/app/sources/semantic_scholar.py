"""Semantic Scholar adapter (academic literature)."""

import logging

from app.core.config import get_settings
from app.sources.base import SourceAdapter, SourceItemData
from app.sources.http import build_client, request_with_retry

logger = logging.getLogger(__name__)

_API_FIELDS = (
    "title,abstract,year,venue,authors,externalIds,url,citationCount,publicationTypes"
)


class SemanticScholarAdapter(SourceAdapter):
    """Official Semantic Scholar Graph API adapter (keyless-capable)."""

    adapter_id = "semantic_scholar"
    display_name = "Semantic Scholar"
    provider_schema_version = "2024-06"
    base_url = "https://api.semanticscholar.org/graph/v1/paper/search"

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.semantic_scholar_api_key

    @property
    def credentials_configured(self) -> bool:
        return not self.credentials_required

    @property
    def credentials_required(self) -> bool:
        return False

    async def search(self, query: str, limit: int = 10) -> list[SourceItemData]:
        headers: dict[str, str] = {}
        if self._api_key:
            headers["x-api-key"] = self._api_key
        async with build_client() as client:
            response = await request_with_retry(
                client,
                self.base_url,
                params={
                    "query": query,
                    "limit": max(1, min(limit, 100)),
                    "fields": _API_FIELDS,
                },
                headers=headers,
                adapter_id=self.adapter_id,
            )
            payload = response.json()
        items = payload.get("data") or []
        results = []
        for item in items:
            external = item.get("externalIds") or {}
            identifiers = {
                "s2_paper_id": item.get("paperId"),
                "doi": external.get("DOI"),
                "arxiv_id": external.get("ArXiv"),
                "url": item.get("url"),
            }
            identifiers = {k: v for k, v in identifiers.items() if v}
            results.append(
                SourceItemData(
                    adapter_id=self.adapter_id,
                    source_kind="paper",
                    title=(item.get("title") or "").strip(),
                    identifiers=identifiers,
                    authors=[a.get("name") or "" for a in (item.get("authors") or [])],
                    venue=item.get("venue"),
                    year=item.get("year"),
                    abstract_or_description=item.get("abstract"),
                    primary_url=item.get("url"),
                    quality_signals={
                        "citation_count": item.get("citationCount"),
                        "publication_types": item.get("publicationTypes") or [],
                    },
                    raw_payload=item,
                )
            )
        return results