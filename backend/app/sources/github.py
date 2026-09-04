"""GitHub adapter (open-source repositories via the official search API)."""

from app.core.config import get_settings
from app.sources.base import SourceAdapter, SourceItemData
from app.sources.http import build_client, request_with_retry


class GithubAdapter(SourceAdapter):
    """Official GitHub repository search adapter (keyless; optional token)."""

    adapter_id = "github"
    display_name = "GitHub"
    provider_schema_version = "2023-06"
    base_url = "https://api.github.com/search/repositories"

    def __init__(self) -> None:
        self._token = get_settings().github_token

    @property
    def credentials_required(self) -> bool:
        return False

    async def search(self, query: str, limit: int = 10) -> list[SourceItemData]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "IdeaLens/0.2 research aggregator",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        params = {"q": query, "per_page": max(1, min(limit, 100))}
        async with build_client() as client:
            response = await request_with_retry(
                client,
                self.base_url,
                params=params,
                headers=headers,
                adapter_id=self.adapter_id,
            )
            items = (response.json() or {}).get("items") or []

        results = []
        for item in items:
            full_name = item.get("full_name") or ""
            owner = (item.get("owner") or {}).get("login") or ""
            license_info = item.get("license") or {}
            created = item.get("created_at") or ""
            results.append(
                SourceItemData(
                    adapter_id=self.adapter_id,
                    source_kind="github_repository",
                    title=full_name,
                    identifiers={
                        "github_repo": full_name,
                        "url": item.get("html_url"),
                    },
                    authors=[owner] if owner else [],
                    venue="GitHub",
                    year=_year(created),
                    abstract_or_description=item.get("description"),
                    primary_url=item.get("html_url"),
                    quality_signals={
                        "stars": item.get("stargazers_count"),
                        "forks": item.get("forks_count"),
                        "language": item.get("language"),
                        "license": (license_info or {}).get("spdx_id"),
                        "updated_at": item.get("updated_at"),
                        "topics": item.get("topics") or [],
                    },
                    raw_payload=_truncate(item),
                )
            )
        return results


def _year(iso_date: str | None) -> int | None:
    try:
        return int((iso_date or "")[:4])
    except ValueError:
        return None


def _truncate(item: dict) -> dict:
    """Keep a bounded raw snapshot (no full code payloads are fetched)."""
    keys = ("full_name", "html_url", "description", "stargazers_count", "language", "topics")
    return {key: item.get(key) for key in keys if key in item}