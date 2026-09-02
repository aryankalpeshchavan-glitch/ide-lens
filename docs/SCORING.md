# IdeaLens — Scoring Philosophy (M0 spec)

**Status:** Conceptual definitions. Legend: **Decision:** = confirmed decision; **Proposed:** = intended future implementation; **Open:** = not yet decided. Exact formulas, weights, and thresholds are tuned against the curated benchmark during implementation (EVALUATION.md). **Decision:** All scores are analytical/ranking signals — never objective scientific truth (ADR-0005).

## 1. Principles

- **P-1 No single "novelty score".** Similarity and gap signals are multidimensional and explainable per dimension.
- **P-2 Deterministic where possible.** AI and embeddings are used only where interpretation is genuinely needed; deterministic code handles validation, normalization, deduplication, integrity checks, scoring calculations where possible, and evidence linkage.
- **P-3 Transparent inputs.** Every score references its inputs: contributing evidence ids, query coverage, the scoring-configuration snapshot, provider/model, and timestamp — so it can be audited and recomputed.
- **P-4 Calibrated, not invented.** Default thresholds and weights start as documented proposals and are tuned against the curated benchmark before any production claim.
- **P-5 Conservative language.** "Limited evidence found" is never rendered as "novel"; gap-bucket wording is standardized (§5–6).
- **P-6 Explainable output.** A score without a human-readable, evidence-cited explanation is a defect.

## 2. Multidimensional similarity

**Decision:** Similarity is computed per dimension: problem, objective, technology, method, architecture, dataset, domain/application. Additional dimensions may be added later. Any dimension may be **NA** when no extractable signal exists.

For each dimension `d`, a similarity assessment has three parts (**Decision**: explanations are mandatory):

1. **Score_d** — a normalized value in [0,1] combining semantic embedding similarity, lexical overlap, structured field match, and coverage quality. Weights: **Open**; proposed default is an equal-weight hybrid.
2. **Confidence_d** — low/medium/high, reflecting evidence availability, extraction confidence, and embedding/AI reliability. Low confidence means the signal is weak regardless of score magnitude.
3. **Explanation_d** — a structured "why": top contributing evidence ids, matched concepts, factors behind the overlap, and caveats.

**Aggregation rules (Decision):**

- No arithmetic "overall novelty" value exists. The report shows a per-dimension table plus qualitative summary (e.g., "Problem similarity: high — …"), never "75% novel".
- Dimensions are shown only when explainable; **NA** is honest output where signals are missing.
- Display bands (Proposed; aids only, calibrated post-benchmark): none/very-low < 0.2; low 0.2–0.4; moderate 0.4–0.6; high 0.6–0.8; very-high ≥ 0.8. Bands carry no scientific-truth meaning.

## 3. Evidence strength

**Decision:** Per Evidence record, strength is a composed view with transparent inputs (exact formula **Open**):

- Directness — how directly the evidence addresses the claim or dimension (dimension match, relevant excerpt present).
- Provenance completeness — original identifier/URL, source metadata, retrieval timestamp, extractor identity (EVIDENCE_MODEL.md).
- Source standing — faceted signals only (peer-review status, citations, repo activity), never an objective-quality score (§4).
- Extraction confidence — schema compliance, excerpt presence, deterministic checks, AI confidence where applicable.

Output: weak / moderate / strong, with the contributing inputs disclosed ("why this strength"). **Decision:** strength never gates inclusion — weak evidence is stored and labeled weak; it only weights emphasis in similarity and gap analysis.

## 4. Source ranking

**Decision:** Source quality signals are displayed as labeled facets, never fused into a single objective score:

- primary vs. secondary source;
- peer-reviewed status when available;
- author metadata; institutional information;
- publication date; citation information;
- source type; directness of evidence;
- repository activity where relevant (stars, forks, commit activity, last update, license).

Facets may serve as a transparent ranking aid — e.g., deterministic tie-breaking or weighting evidence strength — with the facet set disclosed per run in the scoring-configuration snapshot. Exact combination behavior: **Open**, benchmark-calibrated. Facet availability varies by source type and must not silently penalize.

## 5. Research saturation

**Decision:** Saturation is characterized per concept, dimension, or combination — never globally.

Inputs (deterministic where possible): deduplicated evidence count, evidence strength weights, source diversity (distinct sources/venues), recency window, and a **coverage ratio** (queries executed vs. planned; per-source success/failure; retrieval degradation).

**Decision:** Output is one of four buckets:

1. **Common / well represented** — multiple strong, independent evidences across sources.
2. **Moderately represented** — some evidence, mixed strength/diversity.
3. **Limited evidence found** — few or weak evidences. Required phrasing: *"Limited evidence of this combination was found within the retrieved and analysed corpus."* Never "novel", "no prior work", or "first".
4. **Insufficient evidence** — retrieval coverage is too weak to characterize the area. Must state why: few queries, source failures, low coverage ratios, or adapter degradation.

Bucket assignment uses deterministic gate-checks on the inputs so wording stays consistent (exact thresholds **Open**, benchmark-calibrated). **Decision:** a bucket without disclosed coverage evidence is invalid.

## 6. Gap signals

**Decision:** A gap signal is an evidence-based observation that a combination or dimension is comparatively *less represented in the retrieved corpus* — not a novelty claim (ADR-0005).

Rules:

- Gap signals derive from a saturation bucket of "limited evidence found" or weaker, **plus** adequate coverage/recall proxies (multi-source coverage, query coverage, dedup audit).
- Absence of evidence is always reported with mandatory scope caveats. "Insufficient evidence" (bucket 4) is the honest outcome when coverage is poor — never bucket 3 as a substitute.
- Forbidden anywhere in outputs: "first-ever", "no prior work", "vacant space", "nobody has done this", "100% novel", "novel" used as a conclusion. Enforced by report-generation guardrails (EVALUATION.md §8).
- Every gap statement carries its evidence basis and coverage disclosure (DATA_MODEL.md: ResearchGap).

## 7. Contradiction signal strength

**Decision:** A contradiction flag groups conflicting claims or evidences on the same dimension or protocol.

- Both sides are always preserved; no side is silently selected as the "winner".
- Comparability is assessed first: same metric type, same dataset, same evaluation protocol, same experimental conditions? Low comparability → the discrepancy is flagged but labeled **"not directly comparable"** rather than scored as a contradiction.
- Deterministic pre-checks (metric type, dataset id, protocol markers) run before any LLM summarization; a contextual summary then retains both claims with possible explanations: different datasets, evaluation protocols, metrics, train/test splits, experimental conditions, or model versions.

## 8. Scoring configuration & reproducibility

**Decision:** Every run persists a scoring-configuration snapshot: dimensions, weights/proposal version, bands, thresholds, provider and model versions, temperature. Score records reference this snapshot plus their input evidence ids, so any score can be reproduced or audited (DATA_MODEL.md: SimilarityResult).

## 9. Research Coverage

**Decision:** Research Coverage is a measurement/reporting concept that communicates how well the retrieved and analysed evidence covers the important dimensions of the user's idea. It answers "for each dimension of the idea, how much relevant evidence did we obtain and analyse?" — not "is this idea new?".

Assessed dimensions (consistent with the Evidence dimensions; extendable): problem, objective, technology, method, architecture, dataset, deployment, evaluation.

For each dimension, coverage is reported in one of four levels:

1. **Strong** — multiple relevant, independent evidences across sources.
2. **Moderate** — some relevant evidence, mixed strength or diversity.
3. **Limited** — few or weak relevant evidences.
4. **Insufficient** — too little evidence, or retrieval coverage too degraded, to judge; the report must state why (queries executed/planned, per-source failures, adapter degradation).

Deterministic inputs (thresholds **Open**, benchmark-calibrated): per-dimension deduplicated evidence count, evidence strength weights, source diversity, retrieval coverage ratio, and metadata-field availability (e.g., abstract present, venue/year known).

**Caveats (Decision):** Research Coverage refers only to the retrieved and analysed corpus. It must never be interpreted as proof of novelty, and never as an estimate of the completeness of the global research landscape. Wording follows the saturation buckets: "strong / moderate / limited / insufficient evidence on dimension X within the retrieved and analysed corpus."

How Research Coverage differs from related concepts:

- **Research Gap** — Research Gaps characterize whether concepts or combinations are densely or sparsely represented in the retrieved corpus (landscape-level, §5–6). Research Coverage is an evidence-sufficiency view of the user's own idea dimensions for this run. A run can have strong coverage on a dimension and still surface gap signals for specific combinations — or the reverse.
- **Similarity** — Similarity measures how close retrieved work is to the idea along a dimension. Coverage measures how much evidence was obtained per dimension, regardless of how similar it is. High similarity on one dimension with little evidence elsewhere is a common, legitimate combination of signals.
- **Source Quality** — Source quality is a per-source/per-item facet-level property (§4). Coverage is a run-level aggregate across all retrieved evidence for each dimension. Source quality affects strength weighting; coverage reflects the quantity and diversity of evidence, independent of which specific sources were strong.
- **Confidence** — Confidence (extraction/linkage, EVIDENCE_MODEL.md §5) describes the reliability of individual evidence records or links. Coverage describes the sufficiency and diversity of evidence per dimension. High-confidence evidence from a single source still yields limited coverage for that dimension.

Recording: per-dimension Research Coverage is carried in the report's coverage disclosure (DATA_MODEL.md: Report `scope_disclosure`; see also FAILURE_HANDLING.md §10 and EVIDENCE_MODEL.md §6).