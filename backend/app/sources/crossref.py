"""Crossref adapter (literature/DOI metadata via the REST API)."""

import re

from app.sources.base import SourceAdapter, SourceItemData
from app.sources.http import build_client, request_with_retry


def _strip_jats(text: str | None) -> str | None:
    """Strip inline JATS/XML tags from Crossref abstracts, if any."""
    if not text:
        return None
    return re.sub(r"<[^>]+>", " ", text).strip() or None


class CrossrefAdapter(SourceAdapter):
    """Official Crossref REST API adapter (keyless)."""

    adapter_id = "crossref"
    display_name = "Crossref"
    provider_schema_version = "1.0"
    base_url = "https://api.crossref.org/works"

    @property
    def credentials_required(self) -> bool:
        return False

    async def search(self, query: str, limit: int = 10) -> list[SourceItemData]:
        headers = {"User-Agent": "IdeaLens/0.2 (research aggregator; mailto:admin@idealens.local)"}
        params = {
            "query": query,
            "rows": max(1, min(limit, 200)),
            "select": "DOI,title,author,published,container-title,abstract,URL,type",
        }
        async with build_client() as client:
            response = await request_with_retry(
                client,
                self.base_url,
                params=params,
                headers=headers,
                adapter_id=self.adapter_id,
            )
            items = (response.json().get("message") or {}).get("items") or []

        results = []
        for item in items:
            doi = (item.get("DOI") or "").lower()
            title = (item.get("title") or [""])[0]
            year = None
            published = item.get("published", {}).get("date-parts")
            if published and published[0]:
                year = published[0][0]
            results.append(
                SourceItemData(
                    adapter_id=self.adapter_id,
                    source_kind="paper",
                    title=title,
                    identifiers={
                        "doi": doi,
                        "url": item.get("URL") or (f"https://doi.org/{doi}" if doi else None),
                    },
                    authors=_author_names(item.get("author") or []),
                    venue=(item.get("container-title") or [None])[0],
                    year=year,
                    abstract_or_description=_strip_jats(item.get("abstract")),
                    primary_url=item.get("URL") or (f"https://doi.org/{doi}" if doi else None),
                    quality_signals={"type": item.get("type")},
                    raw_payload=item,
                )
            )
        return results


def _author_names(authors: list[dict]) -> list[str]:
    names = []
    for author in authors:
        family = author.get("family") or ""
        given = author.get("given") or ""
        names.append(f"{given} {family}".strip())
    return [name for name in names if name]