"""Tests for source query Redis caching and stable hash provenance."""

from app.infrastructure.cache import (
    compute_query_hash,
    get_cached_sources,
    set_cached_sources,
)
from app.sources.base import SourceItemData


def test_compute_query_hash_is_stable_and_normalized():
    """Hashes must be invariant to whitespace and case variations."""
    h1 = compute_query_hash("Attention Is All You Need")
    h2 = compute_query_hash("   attention is   all you need   ")
    assert h1 == h2
    assert len(h1) == 64


def test_set_and_get_cached_sources(monkeypatch):
    """Source results are stored with provenance and retrieved cleanly."""
    store = {}

    class MockRedis:
        def get(self, key):
            return store.get(key)

        def setex(self, key, ttl, value):
            store[key] = value

        def close(self):
            pass

    monkeypatch.setattr("app.infrastructure.cache.build_redis_client", lambda: MockRedis())

    items = [
        SourceItemData(
            adapter_id="arxiv",
            source_kind="paper",
            title="Transformer Scaling Laws",
            authors=["Alice", "Bob"],
            year=2023,
            identifiers={"arxiv_id": "2301.00001"},
            primary_url="https://arxiv.org/abs/2301.00001",
        )
    ]

    query = "transformer scaling laws empirical analysis"
    assert set_cached_sources("arxiv", query, items) is True

    cached = get_cached_sources("arxiv", query)
    assert cached is not None
    assert len(cached) == 1
    assert cached[0].title == "Transformer Scaling Laws"
    assert cached[0].identifiers == {"arxiv_id": "2301.00001"}
    assert cached[0].year == 2023


def test_cache_gracefully_handles_redis_disconnect(monkeypatch):
    """When Redis is unreachable, cache calls return None/False without crashing."""
    def _failing_redis():
        raise ConnectionError("Redis down")

    monkeypatch.setattr("app.infrastructure.cache.build_redis_client", _failing_redis)

    assert get_cached_sources("arxiv", "test query") is None
    assert set_cached_sources("arxiv", "test query", []) is False
