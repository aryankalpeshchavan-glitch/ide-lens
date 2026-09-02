# IdeaLens — Failure Handling & Resilience (M0 spec)

**Status:** Resilience design. Legend: **Decision:** = confirmed decision; **Proposed:** = intended future implementation; **Open:** = not yet decided. Exact numeric defaults are proposals tuned during implementation.

**Design goal (Decision):** A single unavailable source must not destroy a research run. The final result discloses partial failures and degraded coverage explicitly.

## 1. Error taxonomy

**Decision:** Errors are classified as one of: `NETWORK/TIMEOUT`, `HTTP_5XX`, `HTTP_429` (rate limit), `HTTP_4XX` (auth/not-found/bad-request, non-429), `MALFORMED_PAYLOAD`, `MISSING_CREDENTIALS`, `VALIDATION_ERROR`, `AI_PROVIDER_ERROR`, `AI_SCHEMA_ERROR`, `EMBEDDING_PROVIDER_ERROR`, `WORKER_CRASH`, `STORAGE_ERROR`, `CANCELLED`, `UNKNOWN`.

Every failure record carries: class, stage, component (source adapter or provider), run id, timestamp, retry count, redacted message, and links to logs/metrics.

## 2. Retry policy

**Proposed defaults** (exact values Open, tuned during implementation):

- Transient network errors and HTTP 5xx: exponential backoff with jitter, up to N attempts (Proposed: 3–5), then the stage records failure.
- HTTP 429: honor `Retry-After` when present, otherwise per-source pacing; attempts are capped per run to bound duration.
- HTTP 4xx (non-429): no automatic retry; auth/config problems surface in health checks.
- AI and embedding calls: transient errors retry per the same policy; schema-invalid LLM output triggers a bounded re-prompt (Proposed: ≤ 2), then the stage is partial/failed — nothing fabricated (§7).

**Decision:** stage re-entry is idempotent via persisted artifacts and deterministic checks; enqueueing is at-most-once.

## 3. Timeouts

**Proposed:** Per-outbound-call timeouts (connect/read); per-source budget per query; per-stage budget per run; run-level budget with an explicit "abort vs. degrade" decision, recorded. Per-LLM/embedding call timeouts; queue visibility timeout is set greater than the longest stage so a crashed worker causes a requeue while artifacts prevent double-processing (see §8). Exact values: **Open**.

## 4. Rate-limit handling

**Decision:** Centralized pacing per source (SOURCE_POLICY.md §4): token buckets and queue-drain scheduling avoid burst fan-out; HTTP 429 / `Retry-After` is integrated into the scheduler. Rate-limit events are logged and surfaced in the report ("source X returned rate limits; retrieval coverage reduced"). **Proposed:** on repeated 429s the adapter health degrades, and the orchestrator routes remaining queries to other sources when sensible.

## 5. Partial-source failure

**Decision:**

- Each (source, query) unit is handled independently: failures are isolated, recorded, and counted.
- At run end, `coverage_disclosure` summarizes per source: requests, successes, failures, rate-limit events, cache hits, and a degradation ratio.
- Only when every source for a query or stage fails is the stage marked `degraded`; the run continues if downstream stages can proceed with the available evidence, and the final report discloses the degradation explicitly.
- There are no fabricated substitutes and no silent "no prior work" inference from a failure (SCORING.md §5–6).

## 6. Malformed source handling

**Decision:** Provider payloads are schema-validated at the boundary (Pydantic). Invalid payloads produce a `MALFORMED_PAYLOAD` record and are quarantined and counted; they never crash a run. The orchestrator continues with other sources/items, and the malformed count appears in the coverage disclosure. Raw payloads are referenced (not necessarily stored) for post-hoc replay/debug (SOURCE_POLICY.md §7).

## 7. AI failure

**Decision:** AI call errors, timeouts, and schema-invalid outputs are isolated to their stage (retry policy §2). Schema-invalid LLM output triggers a bounded re-prompt (Proposed: ≤ 2), then the stage is `partially_failed`/`failed` with explicit disclosure — nothing fabricated. AI outputs are deterministically validated where feasible (claim/evidence schema, dimension vocabulary, linkage existence) before use. The report states which stages were affected by AI failure; downstream analysis never silently degrades in semantics.

## 8. Worker failure

**Decision:** Jobs persist in the Redis queue (durable-messaging behavior depends on Redis configuration; see **Open** below). The visibility timeout exceeds the longest stage, so a crashed worker leads to a requeue; re-execution is safe via idempotent stages and persisted artifacts with at-most-once enqueue. Each stage writes its artifacts and state history before proceeding (checkpointing), so a worker resumes from the last persisted stage after a crash (ADR-0003). **Proposed:** a worker crash mid-run leaves the run `running` with a heartbeat; a sweeper transitions stale runs per policy (sweep interval **Open**). **Open:** Redis durable-messaging configuration and whether a secondary queue (e.g., Redis Streams) is used.

## 9. Observability

**Decision:**

- Structured JSON logs carry: run id, stage, component (adapter/provider), error class, retry count, duration, and trace id (**Proposed**: OpenTelemetry-compatible later).
- Metrics: per-source success/error/429/latency; per-stage duration; queue depth; run-outcome distribution; cache hit ratio.
- A per-run append-only event log records events such as `source.rate_limited`, `stage.completed`, `error.recorded` (realized as RunEvent rows in DATA_MODEL.md §2) and is surfaced via API/UI.
- Health endpoints report adapter health, provider-config presence, and queue/database connectivity (**Proposed**).
- Secrets are stored out-of-band (environment / secret manager) and never in code, repo, logs, or docs; the data model stores only a `credentials_configured` boolean (SOURCE_POLICY.md §10).

## 10. Disclosure contracts

**Decision:** The report must always state: per-source coverage; any partial failures; cache-served items; models/providers used; retrieval timestamps (cached vs. fresh); the scoring-configuration hash; per-dimension research coverage levels (SCORING.md §9); and the scope caveat that the retrieved corpus is not the entire field (EVIDENCE_MODEL.md §6).