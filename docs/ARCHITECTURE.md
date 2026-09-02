# IdeaLens — System Architecture (M0 spec)

**Status:** Conceptual architecture. Legend: **Decision:** = confirmed architecture concept; **Proposed:** = intended implementation detail; **Open:** = not yet decided. No application code exists yet.

## 1. Architecture overview

**Decision:** A **modular monolith** (ADR-0001): one backend codebase (FastAPI) hosting the HTTP API and a background worker process type; PostgreSQL as the system of record; Redis as queue and cache; a Next.js frontend calling the API. No microservices, no Kubernetes, no service mesh, no unnecessary distributed infrastructure.

```
Browser (Next.js frontend)
   │ HTTPS/JSON
   ▼
FastAPI application (modular monolith)
   ├── API layer (routes, validation, run lifecycle)
   ├── Domain services (ingestion, decomposition, claims, query planning,
   │                     retrieval orchestration, evidence, analysis, report)
   ├── Source adapters (Semantic Scholar, Crossref, arXiv, GitHub, + future)
   ├── AI provider abstraction (LLMs)
   ├── Embedding provider abstraction
   └── Worker process type (consumes Redis queue; executes run stages)
                    │
   ┌────────────────┼─────────────────┐
   ▼                ▼                 ▼
 PostgreSQL    Redis (queue, cache,   External APIs
                 rate-limit/retry)    (sources, LLMs, embeddings)
```

## 2. Major modules

- **M-1 API layer** — FastAPI endpoints, Pydantic DTOs, auth (M1+), run submission/status/result retrieval, error responses, observability hooks.
- **M-2 Ingestion & parsing** — accept text or TXT/PDF/DOCX uploads; normalize to plain text plus chunks (DocumentChunk); format detection and size guards.
- **M-3 Decomposition & claims** — LLM-assisted extraction of problems, objectives, technologies, methods, datasets, architecture hints, and assumptions into discrete claims; deterministic schema validation afterwards.
- **M-4 Query planning** — generate and persist retrieval queries (variants per dimension/angle); required for reproducibility.
- **M-5 Retrieval orchestration** — fan out to source adapters; collect normalized SourceItems; enforce caching and rate limiting; treat retrieval quality as a primary system risk (PRD R-2, EVALUATION.md §4); query diversity, source diversity, metadata filtering, candidate ranking, semantic reranking, and deduplication feed evidence selection; handle partial failures per FAILURE_HANDLING.md.
- **M-6 Normalization & dedup** — canonicalize identifiers, URLs, titles, authors; deterministic fingerprints plus semantic near-duplicate hints; duplicates linked, never silently dropped.
- **M-7 Evidence extraction** — from retrieved items to structured Evidence records with dimensions, length-capped excerpts, and provenance (EVIDENCE_MODEL.md).
- **M-8 Similarity analysis** — per-dimension similarity (embedding + lexical + structured) with explainable scoring (SCORING.md).
- **M-9 Research/evidence graph** — nodes (sources, evidence, claims, technologies, methods, datasets) plus typed edges (used_by, contradicts, similar_to, addresses_problem, implements_method); represented relationally in PostgreSQL (ADR-0006).
- **M-10 Contradiction detection** — deterministic comparability pre-checks plus contextual conflict summaries; preserves both sides with explanations (SCORING.md §7).
- **M-11 Gap analysis** — saturation buckets with coverage gates (SCORING.md §5–6); emits ResearchGap records.
- **M-12 Idea collision analysis** — combination-level representation analysis (e.g., technologies A/B/C → combination signals); under-represented combinations are flagged as investigation-worthy, never novel.
- **M-13 Idea stress test** — challenge assumptions, feasibility, saturation, evaluation difficulty, deployment constraints, and strong existing implementations (deterministic inventory plus LLM-supported, evidence-referenced synthesis).
- **M-14 Differentiation engine** — evidence-grounded recommendations with overlap disclosure, rationale, evidence, and uncertainty (PRD F-14).
- **M-15 Report generation** — assemble the evidence-grounded report from persisted artifacts with strict language guardrails (ADR-0005); deterministic render with templated sections, including per-dimension research coverage (SCORING.md §9).
- **M-16 Observability & logging** — structured JSON logs, metrics, per-run/stage trace ids, health checks, alert hooks (**Proposed**).

## 3. Request / data flow (end-to-end)

```
POST /research-runs  (idea text or document)
   → auth + validation (Pydantic)
   → persist ResearchRun (status=queued) + Document/chunks
   → enqueue job (Redis) … respond 202 {run_id, status_url}   (no long-lived HTTP)

Worker:
   → claim job → run active
   → Stage A: Decomposition & claims   (LLM-assisted; schema-validated)
   → Stage B: Query planning           (persist Query rows)
   → Stage C: Retrieval                (adapters → cached / rate-limited; partial failure tolerated)
   → Stage D: Normalization & dedup    (canonical SourceItems; duplicates linked)
   → Stage E: Evidence extraction      (structured Evidence + provenance)
   → Stage F: Similarity               (per-dimension scores / confidence / explanations)
   → Stage G: Graph + contradictions   (+ gaps + collisions)
   → Stage H: Stress test + differentiation
   → Stage I: Report generation        (guardrailed language; citations)
   → run = completed (or partially_failed / failed with disclosure)

Client polls GET /research-runs/{id} → status + artifact links; final result
contains the report plus coverage/error disclosure.
```

**Decision:** Every stage is idempotent/re-entrant via persisted artifacts (FAILURE_HANDLING.md).

## 4. Asynchronous research-run lifecycle

**Decision:** States: `queued → running → completed | partially_failed | failed`. Cancellation is possible via job-level support; the MVP UX for it is **Open**.

- **Persistent identity**: every run has a UUID, a status, and full state history (JSONB); runs are never ephemeral (ADR-0003).
- **Stages**: a sequence where each stage persists artifacts before proceeding; a worker resumes from the last persisted stage after a crash (FAILURE_HANDLING.md §8).
- **Progress**: stage-level progress events (e.g., `retrieval.started`, `source.rate_limited`) persist as run events and are exposed by the API (**Proposed**) for the UI.
- **Partial completion**: completed-with-degradation is a first-class outcome. Either the final status is `completed` with a `coverage_disclosure` attached, or `partially_failed` when required stages failed; the report always states what happened.

## 5. Source adapter architecture

**Decision (ADR-0004):** all sources implement a common `SourceAdapter` interface; the orchestrator depends only on the interface — new sources are added without touching the analysis engine.

Conceptual contract (Python typing in M1+):

- `adapter_id`, `display_name`, `provider_schema_version`
- `search(query, run_id, page_token, limit) → paginated canonical results` (ids, identifiers, title, authors, year, venue, abstract/description, primary_url, raw_payload_ref)
- `get_by_id(identifiers)` — optional, where the provider supports it
- metadata: `rate_limit_policy`, `cache_policy`, `credentials_required`, `temporal_policy`
- `health_check()` — reported to orchestration and observability

**Decision:** Orchestrator responsibilities: query-to-source assignment (coverage planning), retries/backoff, rate-limit pacing, caching (adapters label payloads as cacheable), partial-failure handling, and recording everything per run.

Adapter inventory: `semantic_scholar`, `crossref`, `arxiv`, `github` — implemented in M1+, not now.

## 6. AI provider abstraction

**Decision:** All LLM usage flows through an `AIModelProvider` interface so providers can be swapped or config-selected without touching domain logic.

Conceptual contract:

- `id`, `display_name`, `model_version`
- `complete(prompt, schema_definition, temperature≈0, max_tokens) → structured JSON matching schema` (**Proposed** default; exact signature **Open**)
- usage/cost/token accounting hooks; `provider_config_ref` (no secrets in code)

**Decision:** Schema-constrained structured outputs only (JSON Schema). Decomposition, extraction, query generation, and analysis summaries use the abstraction. Deterministic validation always runs on AI output before use; on failure, a bounded re-prompt occurs, then the stage degrades per policy — nothing fabricated (FAILURE_HANDLING.md §7).

## 7. Embedding abstraction

**Decision:** Embeddings are accessed through an `EmbeddingProvider` interface (same spirit as the AI abstraction); semantic similarity is never hard-coded to one provider.

Conceptual contract:

- `id`, `display_name`, `model_version`, `dimensions`
- `embed(text) → vector`; `embed_batch(texts) → vectors`
- `similarity(a, b) → float` (deterministic cosine or other; chosen form **Open**)
- vector caching keyed by content hash + model version; batch support **Proposed**

**Decision:** Embeddings feed per-dimension similarity (SCORING.md §2) and near-duplicate detection hints. Lexical and structured signals always accompany embeddings to reduce provider bias. On embedding failure the stage degrades deterministically — never fabricates (FAILURE_HANDLING.md §7).

## 8. Evidence flow

```
SourceItem → (dimension-matched excerpts) → Evidence (excerpt, span, confidence, provenance)
          ↓ ClaimEvidence (role: supports/contradicts/context; linkage confidence; rationale)
          ↓ Claim → analysis (similarity, contradiction, gap, collision, stress test, differentiation)
          ↓ Report section (citation = stable identifier/URL of SourceItem; every conclusion → evidence refs)
```

**Decision:** Conclusions always resolve to the original source identifier/URL through the chain (EVIDENCE_MODEL.md §6). Excerpts are capped and attributed (SOURCE_POLICY.md §8). Ungrounded statements are explicitly labeled. No orphan scores (SCORING.md §6).

## 9. Failure boundaries

- **Per-outbound-call** (timeout, 429, 5xx) → adapter-local retry/backoff (FAILURE_HANDLING.md §2–3); boundaries isolate one source or provider from the rest of the run.
- **Per-source (adapter)** → after retries, the source is marked failed-for-run; coverage accounting updates; the run continues with remaining sources.
- **Per-stage (domain)** → stage failure makes the run `partially_failed`/`failed` with disclosure; downstream stages that can proceed on available data may do so, with the report clearly stating degradation.
- **Run-level (budget/abort)** → explicit record; never a silent empty-result inference.

## 10. Deployment architecture (conceptual; no infra exists yet)

**Decision:** A modular monolith (ADR-0001) deployed as a single deployable unit (one codebase) with two process types: `api` (FastAPI, serves HTTP) and `worker` (background stage executor). Scale-out happens by adding worker/API replicas behind a simple load balancer (exact infra **Open**).

Components:

- PostgreSQL (managed or self-hosted; **Open**);
- Redis (queue + cache + rate-limit/retry bookkeeping);
- object/blob storage for documents and reports (**Proposed**: S3-compatible or local for development; **Open**);
- small scheduled jobs (e.g., sweeper) **Proposed** to run inside the worker process;
- reverse proxy/TLS and environment-managed secrets;
- no Kubernetes, no service mesh (ADR-0001).