# IdeaLens — Product Requirements Document (PRD)

**Status:** Draft — Milestone 0 (M0). Legend: **Decision:** = confirmed decision; **Proposed:** = intended future implementation; **Open:** = not yet decided. No application code exists yet; this document specifies the intended product.

## 1. Product vision

IdeaLens is an **evidence-driven technical idea intelligence engine** (ADR-0002). A user submits a technical/research/project idea — as plain text or via a TXT/PDF/DOCX document — and IdeaLens investigates the existing technical landscape across multiple academic and open-source sources, then produces an evidence-grounded analysis covering: the problems the idea addresses; existing approaches; technologies and methods already used; datasets already used; existing research; existing open-source implementations; existing practical/commercial solutions where appropriate; overlap between the proposed idea and discovered work; contradictions in the discovered evidence; areas with dense existing work; areas where evidence is comparatively limited; possible combinations that appear less represented; and defensible ways to differentiate the proposed project.

Its purpose is to help people decide what to build or investigate — **not** to deliver verdicts of novelty, originality, or IP safety. IdeaLens surfaces evidence and lets the user judge. It never claims an idea is "100% novel", never treats absence of retrieved evidence as proof that nobody has done something, and never equates similarity with plagiarism or loss of novelty (ADR-0005).

## 2. Problem statement

Teams routinely commit months to projects that overlap heavily with existing research, open-source implementations, or commercial products — without a systematic way to discover that overlap ahead of time. Existing discovery tools fall short:

- **Generic search engines** surface pages, not synthesized evidence; they are poor at structured landscape analysis.
- **Narrow academic databases** ignore the GitHub/open-source ecosystem and the commercial landscape, and require manual multi-site hopping.
- **Manual literature review** is slow, non-reproducible, biased by what the reviewer already knows, and hard to scale across many ideas.

No widely accessible tool combines multi-source retrieval with structured evidence extraction, contradiction detection, gap analysis, and explainable differentiation reasoning — while staying transparent about uncertainty, provenance, and search scope. IdeaLens targets that gap.

## 3. Target users

Primary:

- **Technical founders / indie hackers** — assessing a project idea before committing to build it.
- **Researchers** — scoping a literature landscape or checking overlap before writing a proposal or paper.
- **Engineering teams** — evaluating build-vs-adopt decisions around open-source components and technologies.

Secondary:

- **Students** — preparing thesis or project proposals.
- **Program / R&D managers** — triaging internal idea portfolios with evidence.
- **Investors** — fast technical due-diligence screening (future; out of MVP scope).

## 4. Use cases

- **UC-1 Idea landscape assessment** — Submit an idea (text or document) and receive a structured report: problems addressed, existing approaches, technologies, methods, datasets, research, OSS, commercial solutions where found, overlaps, contradictions, dense areas, limited-evidence areas, possible combinations, differentiation directions. All conclusions are evidence-linked.
- **UC-2 Pre-build collision check** — Before starting a project, check overlap with existing research/OSS/commercial work and assess plausible differentiation (stress test included).
- **UC-3 Literature scoping** — Obtain a snapshot of relevant research across Semantic Scholar, Crossref, and arXiv, with evidence excerpts, provenance, and search-scope disclosure.
- **UC-4 Reproducible audit** — Re-open a past research run to inspect exact inputs, generated queries, sources, evidence, analysis configuration, models used, errors, and partial failures.
- **UC-5 Contradiction review** — See conflicting claims and results preserved side-by-side with possible explanations (different datasets, metrics, protocols), instead of a cherry-picked consensus.
- **UC-6 Gap-scoped exploration** — Identify combinations of technologies/components that appear comparatively under-represented *within the retrieved corpus*, framed as investigation-worthy — never as novel.

## 5. Core features

The core pipeline stages are detailed in ARCHITECTURE.md.

- **F-1 Input ingestion** — accept plain text or TXT/PDF/DOCX uploads.
- **F-2 Document parsing** — normalize to text plus chunks (DocumentChunk) with format detection and size guards.
- **F-3 Problem/idea decomposition and claim extraction** — LLM-assisted, with deterministic schema validation afterwards.
- **F-4 Query planning** — generate and persist retrieval queries (variants per dimension/angle) for reproducibility.
- **F-5 Multi-source retrieval** — via source adapters (initial: Semantic Scholar, Crossref, arXiv, GitHub); the adapter abstraction allows future sources without rewriting the analysis engine.
- **F-6 Source normalization and deduplication** — canonicalize identifiers, titles, and authors; deterministic fingerprints plus semantic near-duplicate hints; duplicates are linked, never silently dropped.
- **F-7 Evidence extraction** — structured Evidence records with dimensions and length-capped excerpts plus provenance.
- **F-8 Semantic/multidimensional similarity** — per-dimension score, confidence, and explanation; no aggregate "novelty score".
- **F-9 Research/evidence graph** — nodes (sources, evidence, claims, technologies, methods, datasets) with typed edges.
- **F-10 Contradiction detection** — flag conflicting claims/evidence while preserving both sides with possible explanations.
- **F-11 Research gap analysis** — evidence-based density characterization mapped to four buckets (SCORING.md), scope disclosed.
- **F-12 Idea collision analysis** — combination-level representation analysis (A, B, A+B, …); under-represented combinations are flagged as worth investigating, never as novel.
- **F-13 Idea stress test** — actively challenge the idea: alternatives, saturation, feasibility, dataset availability, evaluation difficulty, deployment constraints, unsupported assumptions, strong existing implementations, evidence weaknesses, differentiation openings.
- **F-14 Differentiation recommendations** — evidence-grounded: which parts overlap strongly, what appears less represented, why a differentiation may be technically meaningful, what evidence supports it, and what uncertainty remains.
- **F-15 Evidence-grounded report** — human-readable report with cited evidence, disclosed search scope, configuration, models, and failures.
- **F-16 Async run lifecycle** — persistent run identity and status; background processing; polling in MVP; no long-lived HTTP connection.
- **F-17 Cross-cutting** — caching, retries, rate-limit handling, partial-failure tolerance, structured logging, observability, secure secrets handling.
- **F-18 Research coverage reporting** — report per-dimension research coverage (strong / moderate / limited / insufficient) for problem, objective, technology, method, architecture, dataset, deployment, and evaluation, with explicit scope caveats; never presented as novelty or global completeness (SCORING.md §9).

## 6. MVP

The MVP is one complete research-run pipeline — from idea text/document to the evidence-grounded report — with:

- ingest text/TXT/PDF/DOCX (parsing + chunking);
- the four initial adapters (Semantic Scholar, Crossref, arXiv, GitHub) behind the adapter abstraction;
- query planning with persisted queries;
- retrieval orchestration with caching, retries, per-source rate limiting, partial-failure tolerance, and disclosure;
- source normalization and dedup (canonical linking; no silent drops);
- structured evidence extraction with documented provenance;
- multidimensional similarity (per-dimension score/confidence/explanation);
- evidence/research-graph records;
- contradiction detection (both sides preserved);
- gap analysis (four buckets, scope-disclosed, conservative language);
- per-dimension research coverage reporting (SCORING.md §9);
- idea collision analysis;
- idea stress test;
- differentiation recommendations (evidence-grounded, uncertainty disclosed);
- evidence-grounded report generation (conclusion → claim → evidence → source traceability);
- persistent run records (input, queries, sources, retrieval timestamps, evidence, analysis, scoring config, provider/model info, report info, errors, partial failures);
- async lifecycle: create run → queue → background execution → status polling → result retrieval;
- PostgreSQL persistence, Redis queue/cache, FastAPI backend, Next.js/TypeScript/Tailwind frontend (decided stack).

## 7. Non-goals

Product-level non-goals (**Decision**):

1. **No novelty verdicts** — never "100% novel", "first", or "no prior work"; "limited evidence found" ≠ "novel". Similarity is not plagiarism and not IP-infringement proof; scores are analytical/ranking signals, never objective truth (ADR-0005).
2. **No legal or IP opinions** — similarity and overlap are informational signals, not legal determinations.
3. **No uncontrolled web scraping** — official documented APIs and permitted access only (SOURCE_POLICY.md).
4. **No distributed infrastructure** — no microservices, Kubernetes, service mesh, or unnecessary distributed systems (ADR-0001).
5. **No giant autonomous-agent frameworks** — a supervised, staged pipeline; the LLM is not the entire system (ADR-0002).
6. **No human-level literature-review replacement** — a decision-support aid, not a substitute for expert review.
7. **No storing/copying entire copyrighted documents** — metadata, identifiers, URLs, derived structured analysis, and limited excerpts only (SOURCE_POLICY.md §8).
8. **No synchronous long-running research** — asynchronous research runs only (ADR-0003).
9. **No fake test results** — the evaluation benchmark is planned and curated, never fabricated (EVALUATION.md).

M0-specific non-goals: no application code (backend or frontend), no database migrations, no Docker configuration, no CI/CD, no dependency installation, no environment-variable or secret configuration, no API keys, no source-adapter implementation, no embedding or LLM call implementation, no worker code, no authentication implementation, no frontend components.

## 8. Success criteria

Measurable (after implementation, against the curated benchmark — EVALUATION.md):

- **Retrieval precision/recall** vs. curated expected-source sets, reported per source type and per dimension.
- **Claim-to-evidence grounding rate** — every important analytical statement maps to at least one retrievable evidence record with transparent linkage; ungrounded statements are explicitly labeled.
- **Duplicate detection accuracy** — inflated evidence counts from near-duplicate sources are removed via canonical linking with high precision/recall.
- **Report reproducibility** — identical inputs and configuration yield equivalent report signals: deterministic parts identical, LLM parts stable (documented model, temperature ≈ 0); recomputation is possible from persisted snapshots.
- **Partial-failure tolerance** — a single-source outage does not abort a run; the final report discloses degraded coverage (FAILURE_HANDLING.md).
- **Benchmark-gated releases** — no production claims about retrieval/similarity quality without benchmark evidence (EVALUATION.md).
- **Overclaim guardrails** — language violations ("100% novel", "no one has…", "first"…) fail automated checks (EVALUATION.md §8).

Qualitative:

- Users can explain, per dimension, why overlap exists (explainability).
- Users trust the report because every conclusion traces to evidence and search scope is disclosed.
- The system never overstates: "limited evidence found" language is enforced and gap buckets are tied to coverage/confidence signals.
- The report communicates per-dimension research coverage (strong / moderate / limited / insufficient) with explicit scope caveats, never as novelty or global completeness (SCORING.md §9).

## 9. Major risks

- **R-1 Source API instability / rate limits** → adapter isolation, retries/backoff, caching, partial-failure disclosure, per-source QoS metrics.
- **R-2 Retrieval quality is a primary system risk** → if retrieval under-collects or mis-collects, every downstream stage (evidence, similarity, research coverage, gaps, contradictions, differentiation) is weakened regardless of later analysis quality. Controls:
  - *query diversity* — multi-dimensional query planning with variants per dimension/angle (F-4);
  - *source diversity* — multiple adapters with per-source coverage planning and balance (F-5);
  - *metadata filtering* — explicit handling of incomplete metadata so gaps degrade analysis transparently, not silently (SOURCE_POLICY.md §7);
  - *candidate ranking* — deterministic initial ranking using facets and structured signals (SCORING.md §4);
  - *semantic reranking* — bounded, explainable reranking within similarity analysis (SCORING.md §2);
  - *deduplication* — canonical linking so duplicates do not inflate evidence (F-6);
  - *retrieval evaluation* — benchmark-gated precision/recall per source type and per dimension (EVALUATION.md §4).
  - Partial-source failure is tolerated (FAILURE_HANDLING.md §5), but coverage losses are always disclosed so users can appraise scope (ADR-0005).
- **R-3 LLM hallucination / unsupported claims** → evidence-first constraints, deterministic linkage validation, explicit labeling of ungrounded assumptions, provenance-visible report format, benchmark grading.
- **R-4 Embedding quality / semantic mismatch** → embedding provider abstraction, hybrid semantic + lexical + structured signals, deterministic fallbacks, benchmark evaluation of ranking quality.
- **R-5 Duplicates / near-duplicates inflating evidence** → deterministic + semantic dedup with a transparent policy; duplicates linked, never silently dropped.
- **R-6 False "gap" signals from sparse retrieval** → mandatory scope disclosure, four-bucket conservative language, gap confidence tied to query/source coverage, degradation to "insufficient evidence" when coverage is poor (SCORING.md).
- **R-7 User overtrust (treating scores as objective truth)** → UI and docs explicitly frame scores as analytical/ranking aids; no "novelty score"; ADR-0005 language guardrails.
- **R-8 Scope creep toward agent autonomy** → supervised staged pipeline, deterministic control boundaries, ADR discipline.
- **R-9 Sensitive/private user inputs** → privacy posture in SOURCE_POLICY.md; minimal necessary disclosure to third parties; retention/deletion proposal (**Open**: exact product policy).
- **R-10 Docs drift from implementation** → docs are living artifacts, ADRs are amended on architectural change, and the benchmark ties behavior to spec.