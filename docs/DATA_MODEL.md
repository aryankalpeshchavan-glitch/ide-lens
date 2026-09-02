# IdeaLens — Data Model (M0 spec)

**Status:** Conceptual schema — no migrations, no DDL (M0 non-goal). The entity set is decided; attributes are indicative and **Open** to refinement. SQLAlchemy models will map these in M1+.

## 0. Conventions

**Decision:**

- IDs: UUIDv7 (time-ordered); natural external identifiers (doi, arxiv_id, github_repo, …) live in dedicated columns.
- Timestamps in UTC; audit columns (created_at, updated_at); soft-delete where applicable (**Proposed**).
- Everything significant ties to a **ResearchRun** so runs are reproducible; state, scoring configuration, and provider information are snapshotted as JSONB.

### Entity discipline (design principle)

**Decision:** The 19 proposed entities must be justified by actual domain responsibility and traceability needs — never created merely for architectural appearance. Each entity must carry at least one clear responsibility (aggregation root, provenance/join record, canonical concept, or run-scoped artifact) or satisfy a documented traceability requirement. Entities may later be consolidated (merged into existing tables or JSONB) if implementation evidence shows that separate persistence is unnecessary; the entity list is a starting point to be validated in M1, not a fixed target. See also ADR-0002 (evidence-first) and ADR-0006 (relational graph edges).

## 1. Core entities

1. **User** — identity. Auth is M1+; whether anonymous runs are allowed in MVP: **Open**. Attributes: id, email, display_name, status, created_at.
2. **Project** — container for idea(s) and history. id, owner_user_id (nullable), name, description, status, timestamps. Rel: 1–n ResearchRuns; 1–n Documents.
3. **Document** — the uploaded file or pasted text that sources an idea. id, project_id (nullable), kind (text/txt/pdf/docx), content ref (storage), size_bytes, parse_status, hash_sha256, timestamps. Rel: 1–n DocumentChunks; 1–n ResearchRuns.
4. **DocumentChunk** — normalized parse unit. id, document_id, ord_index, content, char_span, token_estimate, hash. Rel: claims/evidence mentions.
5. **ResearchRun** — the core record and root aggregation for reproducibility. id, project_id (nullable), source_document_id (nullable), input_summary (raw idea or document reference), status (queued/running/completed/partially_failed/failed), state_history (JSONB), scoring_config_snapshot (JSONB), provider_snapshot (JSONB: AI + embedding provider/model/version/temperature), started_at, completed_at, error_summary (JSONB), created_by_user_id (nullable). Rel: 1–n of Query, SourceItem, Evidence, Claim, SimilarityResult, Contradiction, ResearchGap, Recommendation, Report, RunEvent, RunErrorRecord.
6. **Query** — a generated retrieval query. id, run_id, query_text, purpose (dimension/angle), variants_group_id (nullable), generation_info (model/provider/config-hash), ordering, status. Rel: n–m SourceItem via RetrievalHit (rank, fetched_at, cache_hit).
7. **Source** — normalized adapter + endpoint context. id, adapter_id (semantic_scholar/crossref/arxiv/github), provider_info (display_name, schema_version), credentials_configured (boolean; no secrets), policy_ref, last_health. Rel: 1–n SourceItems.
8. **SourceItem** — a single retrieved work or repository (canonical record). id, run_id (nullable), global_normalized_id (dedup key), source_kind (paper/repo/…), identifiers (JSONB: doi, arxiv_id, s2_paper_id, github_repo, isbn, url, …), title, authors (JSONB), venue/journal/host, year, abstract_or_description, license/citation/repo-activity fields, raw_payload_ref, retrieved_at, fetch_metadata (JSONB: cache_hit, rate_limited, retries, adapter_version), dedup_status (canonical/duplicate_of), canonical_id (nullable), quality_signals (JSONB: facets only). Rel: n–m Query; 1–n Evidence.
9. **Evidence** — structured extracted fact/passage from a source (EVIDENCE_MODEL.md). id, run_id, source_item_id, dimension (problem/objective/method/technology/architecture/dataset/evaluation_method/results/limitations/deployment_context/other), claim_text, excerpt (length-capped), excerpt_span, extraction_confidence, provenance_backref (JSONB), retrieval_metadata (JSONB), created_by (extractor id/model/config). Rel: 1–1 SourceItem; n–m Claim via ClaimEvidence.

10. **Claim** — a discrete statement the system commits to (from extraction or analysis). id, run_id, text, kind (idea_claim/extracted_claim/analytical_claim/assumption), status (derived/grounded/ungrounded), confidence, created_by (extractor id/config), created_at. Rel: n–m Evidence via ClaimEvidence; links to ResearchGap; graph edges.
11. **ClaimEvidence** — join plus provenance. id, claim_id, evidence_id, role (supports/contradicts/context), strength_weight (per SCORING.md §3), linkage_confidence, linked_by (deterministic rule / AI + verified), linked_at, rationale. **Decision:** every important conclusion requires at least one ClaimEvidence (EVIDENCE_MODEL.md).
12. **Technology** — entity-concept for a tech/tool/framework (e.g., "FastAPI", "PyTorch"). id, canonical_name, aliases (JSONB), category, description, source_count (denormalized), created_at. Rel: n–m SourceItem/Evidence via dimensions; n–m Method/Dataset via graph edges; participates in similarity and collision computations.
13. **Method** — canonical approach/algorithm/framework-concept (e.g., "transformer fine-tuning", "SLAM"). id, canonical_name, aliases, category, description, source_count. Rel: n–m SourceItem/Evidence; n–n Technology; graph edges; collision inputs.
14. **Dataset** — canonical dataset reference (e.g., "ImageNet"). id, canonical_name, aliases, kind (benchmark/proprietary/generated), availability (public/restricted/unknown), description, source_count. Rel: n–m SourceItem/Evidence (uses_dataset, evaluates_on); n–n Method; similarity-dimension input.
15. **SimilarityResult** — per-dimension similarity for a pair (proposed idea ↔ retrieved SourceItem or evidence cluster). id, run_id, comparable_type (source_item/evidence/aggregate), comparable_id, dimension (problem/objective/technology/method/architecture/dataset/domain-or-application), score (float), confidence (low/medium/high), explanation (JSONB: top_evidence_ids, matched_concepts, factors, caveats), scoring_config_hash, created_at. **Decision:** no aggregate "novelty score" exists (SCORING.md §2).

16. **Contradiction** — a conflicting-claims record. id, run_id, claim_a_id, claim_b_id (or evidence pair), dimension, conflict_type (metric_conflict/factual_conflict/methodological_conflict), comparability (comparable/not_directly_comparable), possible_explanations (JSONB: different datasets/metrics/protocols/splits/conditions/model versions), both_sides_preserved (always true by design), supporting_evidence_refs, created_by.
17. **ResearchGap** — evidence-based gap observation (SCORING.md §5–6). id, run_id, scope_kind (dimension/concept/combination), subject_refs (JSONB), saturation_bucket (common/moderate/limited-evidence-found/insufficient-evidence), coverage_disclosure (JSONB: queries, sources, coverage ratios, failures), standardized_language (required phrasing), evidence_basis (JSONB), created_at. **Decision:** never states "novel"/"first"/"no prior work".
18. **Recommendation** — a differentiation recommendation (PRD F-14). id, run_id, target_refs, overlap_summary (evidence-referenced), differentiation_hypothesis (never guaranteed novel), rationale (technical meaning), supporting_evidence_ids (JSONB), remaining_uncertainty (required), evidence_strength (**Open**).
19. **Report** — the generated evidence-grounded report artifact. id, run_id (1:1), format (**Open**: markdown/html), renderer_version, content ref (storage), citations (JSONB), scope_disclosure (JSONB; includes per-dimension research coverage per SCORING.md §9), generated_at, language_guardrail_status (passed/failed; must pass).

## 2. Supporting entities

- **RunEvent** — append-only per-run events (stage.started/completed, source.rate_limited, source.failed, error.recorded) with timestamp and payload (**Decision**: needed; exact shape **Open**).
- **RunErrorRecord** — error instances per run per FAILURE_HANDLING.md §1: class, stage, component, retry count, redacted message, timestamps.
- **RunCoverage** (or the ResearchRun `coverage_disclosure` JSONB) — per-source accounting: requests, successes, failures, rate_limited, cache_hits (**Decision**: needed; shape **Open**).
- **EvidenceGraphEdge** — typed edges between nodes (SourceItem/Evidence/Claim/Technology/Method/Dataset): similar_to, contradicts, uses_dataset, implements_method, addresses_problem — with weight/confidence and provenance. Stored relationally in PostgreSQL (ADR-0006); concrete schema **Open** in M1.
- **Cache tables** — source-payload cache and vector cache (keys per SOURCE_POLICY.md §5 / ARCHITECTURE.md §7); implementation **Open**.

## 3. Relationship summary

```
User 1—n Project;        Project 1—n Document;     Project 1—n ResearchRun
Document 1—n DocumentChunk;  Document 1—n ResearchRun
ResearchRun 1—n {Query, SourceItem, Evidence, Claim, SimilarityResult,
                 Contradiction, ResearchGap, Recommendation, Report (1:1), RunEvent, RunErrorRecord}
Query n—m SourceItem  via RetrievalHit (rank, fetched_at, cache_hit)
SourceItem 1—n Evidence  (canonical; duplicates: canonical_id → canonical SourceItem)
SourceItem n—1 Source    (adapter context)
Evidence  n—m Claim  via ClaimEvidence (role, confidence, rationale)
Claim    n—m Technology / Method / Dataset  via evidence dimensions + graph edges
Technology / Method / Dataset  n—m n  each other  via graph edges (similarity/collision inputs)
```

## 4. Integrity & consistency notes

**Decision:**

- **Run-scoped snapshots**: scoring configuration, provider/model information, temperature, and query-generation information persist per run so results are recomputable (PRD success criteria).
- **Dedup**: canonical_id linkage only; duplicates are never deleted or silently dropped; reports use canonical items (SCORING.md §5).
- **Traceability invariant**: any analytical output references evidence ids; each Evidence references one SourceItem; each SourceItem keeps stable identifiers/URL — a full chain to the original source (EVIDENCE_MODEL.md §6).
- **JSONB for variable schemas** (identifiers, quality_signals, explanations, coverage/disclosure) validated at write by Pydantic (exact indexing strategy **Open**).
- **Deletion/retention** of user content: **Open** (SOURCE_POLICY.md §10); soft-delete proposed where applicable.