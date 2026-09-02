# IdeaLens — Source Policy (M0 spec)

**Status:** Policy concepts are decided unless marked **Proposed:** or **Open:**. No source adapters are implemented yet (M0 non-goal).

## 1. Allowed source categories

**Decision:** Initial supported source adapters:

1. **Semantic Scholar** — academic literature.
2. **Crossref** — literature/DOI metadata.
3. **arXiv** — preprints.
4. **GitHub** — open-source repositories.

**Proposed** future categories (each requires a new adapter and a policy review): patents and standards registries, dataset registries, commercial-product indexes, curated blogs/news.

**Decision:** The system prefers official, documented APIs and permitted access mechanisms. Uncontrolled scraping of arbitrary websites is not allowed.

## 2. API-first approach

**Decision:** Adapters call only the official, documented API of each provider (e.g., Semantic Scholar API, Crossref REST API, arXiv API, GitHub REST/search API) and map provider payloads to the canonical SourceItem schema. Undocumented or speculative endpoints and parameters are never probed.

Credentials: an adapter supports keyless operation when the provider allows it; otherwise credentials are explicit configuration. **Decision:** M0 assumes no credentials exist; a missing credential produces a clear per-source error state, never a silent skip (FAILURE_HANDLING.md §1).

## 3. Permitted access

**Decision:**

- Official APIs only, using documented parameters and provider pagination (cursors, offsets).
- Metadata-level queries first: titles, abstracts, metadata, and code search.
- Full-text harvesting of paywalled or licensed content is **not permitted**. The system uses metadata, identifiers, URLs, abstracts, and appropriately limited excerpts (see §8).
- No aggressive crawling or bulk harvesting beyond provider rate-limit guidance.

## 4. Rate limiting

**Decision:** Per-source clients respect documented provider rate limits: paced requests plus backoff on HTTP 429 and `Retry-After`. Global outbound concurrency caps protect providers and ourselves. Rate-limit events are recorded per source in run metadata and surfaced in the report when they reduced coverage. Exact per-provider numbers: **Open**.

## 5. Caching

**Decision:** Cache normalized raw source payloads keyed by (adapter id, provider schema version, query hash, pagination cursor, date) so repeated runs do not hammer providers. Cache TTL is per provider (Proposed: ~24h; exact values Open); explicit refresh is allowed.

Cache hits are recorded in provenance and flagged in the report ("cache-served") so reproducibility stays honest. Freshness is governed by the run timestamp plus query coverage, and is always user-visible in the scope disclosure.

## 6. Attribution

**Decision:** Every evidence record retains the original source identifier/URL, the source adapter id, the retrieval timestamp, and provider attribution strings where required. Report citations prefer stable identifiers — DOI, arXiv ID, S2 paper ID, GitHub repo URL — over bare free-text titles where available. License/attribution fields returned by providers are stored when available (e.g., GitHub license, Crossref license links).

## 7. Metadata handling

**Decision:** Provider payloads are normalized to a canonical SourceItem schema: source_kind, provider_item_id, identifiers (jsonb), title, authors (jsonb), venue/journal/host, year, abstract_or_description, license and citation/repo-activity fields where applicable, raw_payload_ref, fetched_at. Raw payload snapshots are referenced, not necessarily mirrored; retention window: **Open** (proposed: limited).

Incomplete metadata is preserved as-is with missing fields recorded; analysis degrades gracefully and never crashes (FAILURE_HANDLING.md §6). Deduplication uses canonical plus duplicate linkage — duplicates are linked, never silently dropped (DATA_MODEL.md §4).

## 8. Copyright considerations

**Decision:** The system does not copy entire documents, papers, or repository contents into the database. Stored content is limited to metadata, identifiers, URLs, derived structured analysis, and limited evidence excerpts — abstracts, descriptions, or snippets relevant to an extracted evidence dimension, length-capped (**Proposed** cap ~500 characters per passage; exact cap Open). Excerpts from non-open-access sources stay within the metadata/brief-snippet regime. Attribution and backlinks always accompany stored excerpts. Provider ToS are respected; adapters encode ToS-level constraints per source (Proposed: per-source policy manifests; mechanism Open).

## 9. Failure behavior

**Decision:** Per-source failures are isolated to that source: recorded, retried per policy, and the run continues with remaining sources (FAILURE_HANDLING.md). Only when every source for a query or stage fails is the stage marked degraded or partial, with explicit disclosure. There are no fabricated substitute results and no silent empty-"no-prior-work" inferences. Malformed data never crashes a run: it is logged, quarantined, and counted.

## 10. Privacy

**Decision:** User-submitted idea text and uploads are stored per DATA_MODEL. Retention/deletion endpoints are proposed for M1+; exact product policy: **Open**. Content is never sold or shared. Third-party APIs receive only the necessary query material — not entire private documents beyond what the chosen provider's processing requires — with disclosure in a privacy notice (**Proposed**). Secrets are never stored in code, repo, logs, or docs (FAILURE_HANDLING.md §9).