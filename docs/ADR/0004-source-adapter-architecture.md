# ADR-0004: Source Adapter Architecture

**Status:** Accepted (M0 decision). **Date:** 2026-09-01 (M0).

## Context

IdeaLens retrieves from multiple, heterogeneous external sources — initially Semantic Scholar (academic literature), Crossref (literature/DOI metadata), arXiv (preprints), and GitHub (open-source repositories). Adapters are currently conceptual and not implemented (M0 non-goal). Each source differs in API shape, credentials, pagination, rate limits, response schemas, identifier schemes, and metadata quality. Future sources (patents/standards, dataset registries, commercial-product indexes, curated blogs/news) may be added (SOURCE_POLICY.md §1).

Sources may fail independently; partial failure must be tolerated (FAILURE_HANDLING.md §5), and the analysis engine must not be rewritten when a source is added, changed, or removed.

## Decision

Introduce a **source-adapter abstraction**:

- A common `SourceAdapter` interface (conceptual contract in ARCHITECTURE.md §5) with: identity (`adapter_id`, `display_name`, `provider_schema_version`); `search(...)` returning paginated canonical results; optional `get_by_id(...)`; per-adapter metadata (`rate_limit_policy`, `cache_policy`, `credentials_required`, `temporal_policy`); and `health_check()`.
- The retrieval orchestrator depends only on the interface: query-to-source assignment, retries/backoff, rate-limit pacing, caching, partial-failure handling, and per-run recording live in the orchestrator, not in the adapters.
- All adapters normalize provider payloads into the canonical `SourceItem` schema (identifiers as jsonb, title, authors, venue, year, abstract/description, URL, raw_payload_ref, fetched_at; DATA_MODEL.md).
- Initial adapter set: `semantic_scholar`, `crossref`, `arxiv`, `github` — implemented in M1+, not now.
- Access policy: official, documented APIs only; an adapter may run keyless where the provider allows; credentials are modeled as a `credentials_configured` boolean, and secrets never live in code (SOURCE_POLICY.md §2, §10).

## Alternatives considered

- **Hard-coded per-source retrieval in the engine:** fastest to prototype one source, but every new source means engine edits, analysis coupling, and accruing mess. **Rejected.**
- **Generic search aggregator (no per-source schema understanding):** uniform but lossy — identifier and quality metadata discarded, degradation invisible. **Rejected** in favor of the canonical schema with raw payload refs and identifiers.
- **Shared scraper layer for all sources:** violates the API-first rule, is fragile, and carries legal/ToS risk (SOURCE_POLICY.md §1, §3). **Rejected.**
- **Dynamically hot-loadable adapter plugins:** over-engineering at this stage; a plain module registry suffices (exact registry mechanism **Open**). **Deferred.**

## Consequences

- **Positive:** sources can be added, changed, or removed without touching the engine; per-source failure isolation supports partial-source failure tolerance; per-source policies (rate limits, cache, temporal) are declarative; per-adapter observability; canonical schemas simplify dedup and evidence extraction.
- **Negative/costs:** interface and normalization overhead per source; adapter quality differences must be measured per source type in evaluation (EVALUATION.md §4); provider schema drift requires adapter maintenance; contract rigidity risk — mitigated by deliberately evolving the interface under ADR discipline.

## Related

ADR-0001, ARCHITECTURE.md §5, SOURCE_POLICY.md, FAILURE_HANDLING.md §4–§5, DATA_MODEL.md (Source, SourceItem), EVALUATION.md §4.