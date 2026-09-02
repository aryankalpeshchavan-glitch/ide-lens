# ADR-0002: Evidence-First Architecture

**Status:** Accepted (M0 decision). **Date:** 2026-09-01 (M0).

## Context

IdeaLens must produce trustworthy, explainable, evidence-grounded analyses. Without discipline, LLM summaries drift into unsupported claims, scores get treated as objective truth, overlap gets mislabeled as novelty, and conclusions lose traceability to sources.

Constraints: every important analytical conclusion must trace to evidence → source → original identifier/URL; evidence must be structured (dimension-tagged), not just "title + URL + score"; duplicates must be handled transparently; similarity must be multidimensional and explainable; gap claims must be scope-disclosed; and no novelty verdicts are ever allowed (ADR-0005).

## Decision

Adopt an **evidence-first architecture**:

1. **Structured evidence as first-class records** — canonical `Evidence` rows with dimension metadata, length-capped excerpts, extraction confidence, and a provenance backbone (EVIDENCE_MODEL.md).
2. **Claims link to evidence via explicit linkage** — a `ClaimEvidence` join with role, confidence, and rationale; every important conclusion requires at least one linked evidence; ungrounded statements are explicitly labeled (DATA_MODEL.md).
3. **Traceability invariant** — conclusion → claim → evidence → source item → stable identifier/URL, enforced at schema and report-generation level (EVALUATION.md §5, §8).
4. **Deterministic-first processing** — validation, normalization, deduplication, data-integrity checks, scoring calculations where possible, and evidence linkage run in deterministic code (SCORING.md §1). AI handles interpretation and extraction only, through an `AIModelProvider` abstraction.
5. **The LLM is not the entire system** — a supervised, staged pipeline: each AI output is schema-validated deterministically before use; failures degrade per policy rather than fabricating (FAILURE_HANDLING.md §7).

## Alternatives considered

- **LLM-generates-everything (a single prompt producing the whole report):** fast, but conflates retrieval, extraction, analysis, and presentation — hallucination risk, non-reproducibility, untraceable claims. **Rejected** (violates the core product premise).
- **Pure retrieval passthrough (render sources only):** maximum fidelity, but fails the product promise of synthesized evidence, contradictions, gaps, and collision analysis. **Rejected as insufficient.**
- **Vector-store-only evidence bag (embedding similarity as the sole signal):** favors opaque scoring and provider bias; fails explainability and multidimensionality. **Rejected** — a hybrid of lexical, structured, and embedding signals is used (SCORING.md §2).
- **Freeform "we will link citations later":** link hygiene cannot be fixed post-hoc; provenance must be designed in. **Rejected.**

## Consequences

- **Positive:** auditable, reproducible runs (provider/model snapshots, scoring-configuration snapshots); explainable similarity (per-dimension score + confidence + explanation); trustworthy gap/contradiction language; easier benchmark grading; graceful degradation of retrieval/extraction failures with disclosure.
- **Negative/costs:** more pipeline stages and schema rigor than a naive LLM wrapper; every AI stage needs deterministic validation; report generation is constrained by linkage checks — more engineering and latency; some nuance of unstructured prose is lost when forced into structured evidence (mitigated by retaining excerpts and rationale).

## Related

ADR-0005 (no-novelty), ADR-0003, ARCHITECTURE.md §2 and §8, EVIDENCE_MODEL.md, SCORING.md, DATA_MODEL.md.