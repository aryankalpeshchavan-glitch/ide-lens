"""Normalization and deduplication (ARCHITECTURE.md M-6).

Normalizes identifiers/titles into canonical forms and fingerprints every
item. Duplicates are linked via ``canonical_id`` and ``dedup_status`` — never
silently dropped (DATA_MODEL.md §4). Near-duplicate hints use the canonical
fingerprint; semantic embeddings can complement this later.
"""

import hashlib
import re


def normalize_doi(value: str) -> str:
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", value.strip().lower())


def normalize_arxiv_id(value: str) -> str:
    return value.strip().split("v")[0].lstrip("/")


def normalize_github_repo(value: str) -> str:
    return value.strip().lower().rstrip("/").replace("https://github.com/", "")


def canon_identifier(identifiers: dict) -> str:
    """Return the strongest stable identifier for an item, or empty string."""
    if identifiers.get("doi"):
        return normalize_doi(str(identifiers["doi"]))
    if identifiers.get("arxiv_id"):
        return normalize_arxiv_id(str(identifiers["arxiv_id"]))
    if identifiers.get("github_repo"):
        return normalize_github_repo(str(identifiers["github_repo"]))
    return ""


def title_key(title: str) -> str:
    """Deterministic title fingerprint: alphanumeric, lowercased, collapsed."""
    cleansed = re.sub(r"[^a-z0-9]+", " ", title.lower())
    tokens = [t for t in cleansed.split() if t not in _TITLE_STOPWORDS]
    return " ".join(tokens)


_TITLE_STOPWORDS = {"a", "an", "the", "of", "and", "for", "on", "in", "with", "toward", "towards"}


def content_hash(title: str, abstract: str | None) -> str:
    blob = f"{title_key(title)}|{(abstract or '')[:4000].lower()}"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:24]


def normalize_source_item(adapter_id: str, item) -> dict:
    """Map a canonical SourceItemData into persisted row fields."""
    identifiers = dict(item.identifiers or {})
    normalized_identifiers = {
        "doi": normalize_doi(str(identifiers["doi"])) if identifiers.get("doi") else None,
        "arxiv_id": (
            normalize_arxiv_id(str(identifiers["arxiv_id"]))
            if identifiers.get("arxiv_id")
            else None
        ),
        "github_repo": (
            normalize_github_repo(str(identifiers["github_repo"]))
            if identifiers.get("github_repo")
            else None
        ),
        "url": identifiers.get("url"),
        "provider_item_id": identifiers.get("s2_paper_id") or identifiers.get("provider_item_id"),
    }
    cleaned = {k: v for k, v in normalized_identifiers.items() if v}

    stable = canon_identifier(cleaned)
    if stable:
        fingerprint = stable
    else:
        fingerprint = content_hash(item.title, item.abstract_or_description)
    global_id = f"{adapter_id}:{fingerprint}"

    return {
        "adapter_id": adapter_id,
        "global_normalized_id": global_id,
        "source_kind": item.source_kind,
        "identifiers": cleaned,
        "title": item.title.strip() if item.title else "",
        "authors": list(item.authors or []),
        "venue": item.venue,
        "year": item.year,
        "abstract_or_description": item.abstract_or_description,
        "primary_url": item.primary_url,
        "raw_payload": dict(item.raw_payload or {}),
        "quality_signals": dict(item.quality_signals or {}),
        "dedup_status": "canonical",
    }


def fingerprint_group(fields: dict) -> str:
    """Group key used for dedup within a run (identifier or title hash)."""
    stable = canon_identifier(fields.get("identifiers") or {})
    if stable:
        return stable
    return content_hash(fields.get("title") or "", fields.get("abstract_or_description") or "")