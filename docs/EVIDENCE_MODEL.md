# IdeaLens — Evidence Model (M0 spec)

**Status:** Conceptual spec. Legend: **Decision:** = confirmed decision; **Proposed:** = intended future implementation; **Open:** = not yet decided. No code exists yet; this defines the evidence semantics the implementation will follow (M1+).

## 1. Evidence

**Decision:** Evidence is a structured, provenance-carrying unit of extracted information from a single retrieved source that supports, contradicts, or contextualizes a claim about the technical landscape relative to the proposed idea. Evidence is *not* just "title + URL + score" — it is dimension-tagged, excerpt-carrying, and linked (see ADR-0002).

An Evidence record (conceptual; see DATA_MODEL.md §1):

- `dimension` — one of: problem, objective, method, technology, architecture, dataset, evaluation_method, results, limitations, deployment_context, other.
- `claim_text` — the derived statement this evidence bears on.
- `excerpt` — a length-capped relevant passage (limit per SOURCE_POLICY.md §8).
- `excerpt_span` — offset within the abstract/description when available.
- `extraction_confidence` — low/medium/high (see §5).
- `provenance_backref` — normalized identifiers (DOI, arXiv ID, Semantic Scholar ID, GitHub repo, URL) of the source, beside the foreign key to SourceItem.
- `retrieval_metadata` — query id, fetched_at, cache_hit, rate-limit/retry info (see §6).
- `created_by` — extractor identity (AI provider/model/revision, or deterministic rule).
- `quality_signals_ref` — faceted source-quality signals (SCORING.md §4; optional).

## 2. Source

**Decision:** A **Source** is the normalized retrieval context of one adapter + endpoint (e.g., "Semantic Scholar API", "arXiv API"). A **SourceItem** is a single retrieved work or repository (paper, repo, etc.) — canonicalized, deduplication-linked via `canonical_id`, and attributed with stable identifiers, metadata, a raw-payload reference, and `fetched_at` (DATA_MODEL.md §1).

Each Evidence references exactly one SourceItem (which knows its Source), so every result keeps a complete chain back to the original identifier/URL.

## 3. Claim

**Decision:** A **Claim** is a discrete statement the system commits to, from any extraction or analysis stage. Every claim carries a kind (`idea_claim`, `extracted_claim`, `analytical_claim`, `assumption`), a status:

- **grounded** — linked to at least one Evidence via ClaimEvidence;
- **ungrounded / assumption** — explicitly labeled as such, never presented as evidence-backed.

## 4. Claim–evidence relationship

**Decision:** Modeled via a **ClaimEvidence** join (DATA_MODEL.md §11) with: `role` (supports / contradicts / context), `strength_weight` (per SCORING.md §3), `linkage_confidence`, `linked_by` (deterministic rule or AI-assisted and verified), `linked_at`, and `rationale` — why this evidence bears on this claim.

Rules:

- Many-to-many: a claim may rest on multiple evidences; an evidence may support multiple claims — per-link provenance is preserved.
- Every important conclusion requires at least one ClaimEvidence record. Ungrounded statements are explicitly labeled.
- Linkage is established deterministically where feasible (identifier, field, keyword, dimension matches); AI-assisted semantic linkage is always verified against evidence dimensions before persisting. Exact heuristics: **Open**, resolved during M1 pilot.
- Contradicting claims keep their own evidences and are preserved side-by-side; no winner is silently selected (SCORING.md §7).

## 5. Evidence confidence

Three distinct confidence notions (**Decision:** never merged into a single objective number):

1. **Extraction confidence** (per evidence) — how reliably the passage was extracted and dimension-classified: schema compliance, excerpt presence, deterministic checks, plus AI confidence where applicable. low/medium/high.
2. **Linkage confidence** (per ClaimEvidence) — how reliably the evidence-to-claim link is correct. low/medium/high.
3. **Strength** (per evidence) — a composed view for weighting (directness, provenance completeness, source standing, extraction confidence). weak/moderate/strong. Strength never gates inclusion; it only weights emphasis (SCORING.md §3).

## 6. Retrieval metadata & traceability

**Retrieval metadata** is recorded per retrieval event: query id, source adapter id, pagination/cursor, fetched_at, cache_hit, rate-limit/retry info, raw payload reference, and provider attribution. It is surfaced in the report's coverage disclosure (FAILURE_HANDLING.md §10).

**Traceability requirement (Decision):** every conclusion, claim, and evidence resolves to the original source through a complete chain:

```
Conclusion → Claim → ClaimEvidence → Evidence → SourceItem → stable identifier / URL
```

- Report citations prefer stable identifiers (DOI, arXiv ID, S2 paper ID, GitHub URL) over bare titles (SOURCE_POLICY.md §6).
- The report always discloses search scope — sources, queries, coverage, failures — and states that the retrieved corpus is not the whole field (ADR-0005).
- The report also communicates per-dimension **Research Coverage** — strong / moderate / limited / insufficient — for the idea's dimensions (problem, objective, technology, method, architecture, dataset, deployment, evaluation), with the caveat that coverage refers only to the retrieved and analysed corpus, never novelty or global completeness (SCORING.md §9).
- Ungrounded statements are labeled and never masquerade as evidence-backed.
- Retention/deletion of raw payloads and source items does not break traceability of persisted evidence (evidence retains `provenance_backref` and citations), subject to the retention policy (**Open**; SOURCE_POLICY.md §10).

## Related documents

DATA_MODEL.md, SCORING.md, ADR-0002, ADR-0005, ADR-0006.