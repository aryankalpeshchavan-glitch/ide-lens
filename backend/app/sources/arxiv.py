"""arXiv adapter (preprints via the official ATOM API)."""

import logging
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

from app.sources.base import SourceAdapter, SourceItemData
from app.sources.http import build_client, request_with_retry

logger = logging.getLogger(__name__)

_ATOM = "http://www.w3.org/2005/Atom"
_ARXIV = "http://arxiv.org/schemas/atom"


def _text(element: ET.Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


class ArxivAdapter(SourceAdapter):
    """Official arXiv API adapter (keyless)."""

    adapter_id = "arxiv"
    display_name = "arXiv"
    provider_schema_version = "1.0"
    base_url = "https://export.arxiv.org/api/query"

    @property
    def credentials_required(self) -> bool:
        return False

    async def search(self, query: str, limit: int = 10) -> list[SourceItemData]:
        params = {
            "search_query": f'all:"{query[:200]}"',
            "start": 0,
            "max_results": max(1, min(limit, 100)),
            "sortBy": "relevance",
        }
        headers = {"User-Agent": "IdeaLens/0.2 research aggregator"}
        async with build_client() as client:
            response = await request_with_retry(
                client,
                self.base_url,
                params=params,
                headers=headers,
                adapter_id=self.adapter_id,
            )
            text = response.text

        root = ET.fromstring(text)
        entries = root.findall(f"{{{_ATOM}}}entry")
        results = []
        for entry in entries:
            identifier = _text(entry.find(f"{{{_ATOM}}}id"))
            arxiv_id = _extract_arxiv_id(identifier)
            doi = _text(entry.find(f"{{{_ARXIV}}}doi")) or None
            identifiers = {"arxiv_id": arxiv_id, "url": identifier}
            if doi:
                identifiers["doi"] = doi
            authors = [
                _text(a.find(f"{{{_ATOM}}}name"))
                for a in entry.findall(f"{{{_ATOM}}}author")
            ]
            published = _text(entry.find(f"{{{_ATOM}}}published"))
            results.append(
                SourceItemData(
                    adapter_id=self.adapter_id,
                    source_kind="preprint",
                    title=_collapse(_text(entry.find(f"{{{_ATOM}}}title"))),
                    identifiers={k: v for k, v in identifiers.items() if v},
                    authors=[a for a in authors if a],
                    venue="arXiv",
                    year=_year(published),
                    abstract_or_description=_collapse(_text(entry.find(f"{{{_ATOM}}}summary"))),
                    primary_url=identifier or None,
                    quality_signals={},
                    raw_payload=_extract_raw(entry),
                )
            )
        return results


def _extract_arxiv_id(identifier: str) -> str:
    """Strip scheme/host and version suffix from an arXiv abs URL."""
    if not identifier:
        return ""
    path = urlparse(identifier).path
    last = path.rstrip("/").split("/")[-1]
    return last.split("v")[0] if last else ""


def _year(iso_date: str) -> int | None:
    try:
        return int(iso_date[:4])
    except (TypeError, ValueError):
        return None


def _collapse(text: str) -> str:
    return " ".join(text.split())


def _extract_raw(entry: ET.Element) -> dict:
    return {
        "id": _text(entry.find(f"{{{_ATOM}}}id")),
        "title": _text(entry.find(f"{{{_ATOM}}}title")),
        "published": _text(entry.find(f"{{{_ATOM}}}published")),
    }