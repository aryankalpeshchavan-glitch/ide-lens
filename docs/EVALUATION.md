# IdeaLens — Evaluation Strategy (M0 spec)

**Status:** Plan only. **Decision:** The manually curated benchmark is *not* created in M0.

## 1. Benchmark philosophy

**Decision:**

- **Manual curation over auto-generation.** Ground truth is human-verified: known technical/project ideas with expected concepts, relevant sources, technologies, methods, datasets, overlaps, and evidence relationships.
- **Behavior-first.** The benchmark measures system behavior — retrieval, extraction, linkage, ranking — against known facts, not subjective impressions.
- **Honest scope.** Recall is computed against the benchmark corpus and admitted as such. The retrieved corpus is never equated with the whole field (ADR-0005).
- **Living artifact.** The benchmark grows with curated cases, is versioned, and is reviewed like code. It lives in the repository (Proposed under `benchmark/`; exact path **Open**). English-first for v1; multilingual is **Open**.

## 2. Benchmark structure

Each curated case contains (**Proposed**):

- the idea fixture (text or document);
- expected concepts: problems, objectives, methods, technologies, datasets, domains;
- expected key sources (DOI, arXiv ID, GitHub repo) with their role and evidence relationships;
- expected overlaps and combinations (collision/gap targets);
- expected contradictions where applicable;
- expected gap characterizations (saturation buckets with scoped language);
- expected differentiation directions;
- ground-truth confidence per item (authoritative vs. plausible).

Ground-truth items are tagged by dimension, source type, and assertion granularity, enabling per-dimension and per-source-type metrics. Fixtures avoid copyrighted full texts: they use abstracts, metadata, and snippets per SOURCE_POLICY.md.

## 3. Evaluation datasets

**Proposed:** Seed set of ~30–50 hand-curated cases (exact count **Open**), spanning:

- academic-heavy ideas (paper landscapes), OSS-heavy ideas (GitHub landscapes), and mixed ideas;
- edge cases: near-duplicate ideas, vague ideas, unsupported-assumption ideas, multi-domain combinations, and contradiction-rich domains (metric conflicts).

**Decision:** Split into train (development), validation (threshold/weight tuning), and test (frozen for final reporting). Never tune on test. Ground truth is verified at curation time; retrieval is judged on stable identifiers (DOI, arXiv ID, repo URL).

## 4. Retrieval quality measurement

**Decision:** Retrieval quality is a **primary system risk** and is measured directly: if retrieval under-collects or mis-collects, every downstream stage (evidence, similarity, research coverage, gaps, contradictions, differentiation) is weakened regardless of later analysis quality. The retrieval quality stack comprises query diversity, source diversity, metadata filtering, candidate ranking, semantic reranking, deduplication, and retrieval evaluation. The benchmark measures each:

- Precision@k and Recall@k against the curated expected-source set, measured on deduplicated canonical ids (retrieval evaluation).
- Per-source-type breakdown (semantic-scholar, crossref, arxiv, github): adapters are judged individually and jointly (source diversity).
- Query diversity: checks that planned queries cover all idea dimensions and angles; a **missing-angle audit** flags dimensions with no dedicated queries.
- A **missing-source audit**: cases where an expected source exists but was not retrieved. This is a critical signal driving query planning, metadata filtering, candidate ranking, and adapter tuning.
- Metadata filtering: the proportion of retrieved items with metadata complete enough for evidence extraction (abstract/description, year, venue, identifiers); low completeness degrades coverage and must be reported.
- Candidate ranking and semantic reranking: measured via the ranking metrics in §6 (e.g., NDCG/MRR over per-dimension ranked evidence sets), with human spot-checks.
- Query coverage: the fraction of planned queries that produced usable results — reported, not just scored.
- Duplicate inflation: near-duplicate count after dedup vs. raw; ground-truth duplicates must collapse to canonical, and duplicates are never silently dropped (deduplication).
- Research coverage consistency: reported per-dimension research coverage levels (SCORING.md §9) must match the underlying retrieved evidence counts in curated cases.

## 5. Evidence grounding metrics

**Decision:**

- **Grounding rate** — the share of analytical statements in reports tied to at least one ClaimEvidence with retrievable evidence. Ungrounded statements must be explicitly labeled.
- **Claim–evidence faithfulness** — expert-judged whether the evidence actually supports the claim, not merely that a link exists (scale piloted in M1; exact protocol **Open**).
- **Evidence extraction accuracy** — correct dimension assignment and correct excerpt selection (starting point: sampled expert review; exact protocol **Open**).
- **Traceability completeness** — the percentage of conclusions with a fully resolved chain: conclusion → claim → evidence → source identifier/URL (EVIDENCE_MODEL.md §6).

## 6. Similarity evaluation

**Decision:**

- Ranking quality against expected overlaps, using at least one ranking metric (e.g., NDCG/MRR over per-dimension ranked evidence sets) plus human spot-checks. The final metric set is finalized during the M1 pilot.
- **Dimension-level calibration** — for expected-dimension cases, true-positive evidence must rank above distractor evidence for that dimension.
- **Explanation sanity** — sampled explanations are flagged when evidence citations are missing or contradict the score (post-hoc checks; exact sampling **Open**).
- **Band sanity** — display bands (SCORING.md §2) must not contradict bucket/confidence labels in curated cases.

## 7. Future human evaluation

**Proposed** (formal protocol **Open**):

- Expert panels score reports blind to ground truth: helpfulness, faithfulness to evidence, clarity of uncertainty, and usefulness of differentiation.
- Paired "AI report vs. expert scope" comparisons on a small curated set; no claim of replacing expert review (PRD non-goal).
- Optional user surveys on whether scope/uncertainty disclosures were understandable.

## 8. Automated guardrails

**Decision:** Run automatically in CI once CI exists (M1+):

- **Language guardrails** — automated checks ban in product outputs: "100% novel", "first-ever", "no prior work", "nobody has done this", "vacant", "unexplored", "novel" as a conclusion, "guarantee", "proves novelty", and "objective truth" (ADR-0005).
- **Linkage guardrails** — every important statement in a report payload must reference evidence ids; missing links block or label the report.
- **Coverage guardrails** — any "limited evidence found" bucket must cite a coverage disclosure; otherwise the report is blocked (SCORING.md §5–6).
- **Coverage-language guardrails** — research coverage levels are reported with scope caveats and never as novelty or global completeness (SCORING.md §9).

## 9. Release gates

**Proposed:** M1 development baseline: no production claims about retrieval, research coverage, similarity, or gap quality without benchmark evidence. A beta is gated on seed-set thresholds (exact thresholds **Open**). Test-set results are published per release announcement (Decision: publish results; format **Open**).