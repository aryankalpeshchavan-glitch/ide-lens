# ADR-0005: No Novelty Guarantees

**Status:** Accepted (M0 decision). **Date:** 2026-09-01 (M0).

## Context

IdeaLens retrieves evidence from a bounded set of sources via search APIs — a retrieved corpus, never the entire field. A naive system could infer "we found nothing, therefore nobody did this", treat similarity as plagiarism or IP infringement, or fuse scores into a single "novelty percentage" presented as objective truth. All of these are scientifically indefensible and product-harmful: they overclaim, invite legal misunderstanding, and cause user overtrust.

## Decision

IdeaLens **never claims novelty**:

1. **Never "100% novel".** An absolute novelty verdict is forbidden; absence of retrieved evidence is not evidence that nobody has done something.
2. **"Limited evidence found" ≠ "novel".** Standardized language is used: *"Limited evidence of this combination was found within the retrieved and analysed corpus."* — always with scope disclosure (SCORING.md §5–6).
3. **Similarity is not plagiarism, not IP infringement, and not proof of lack of novelty.** Similarity signals are informational, never legal or novelty determinations (PRD non-goal).
4. **Scores are analytical/ranking signals — never objective scientific truth.** There is no aggregate "novelty score"; similarity is per-dimension with score, confidence, and explanation; source "quality" is shown as labeled facets, not a fused objective score (SCORING.md).
5. **Enforced by design.** Report-generation language guardrails, linkage guardrails, and coverage guardrails run as automated checks (EVALUATION.md §8); UI and docs frame outputs accordingly (PRD risk R-7).

## Alternatives considered

- **No guardrails (trust LLM wording):** cheapest, but output drift toward overclaims and user harm. **Rejected** (see ADR-0002).
- **A single "novelty score" (percentage):** seductively simple UI, but false precision, unexplainable, and contradicts the multidimensional-similarity requirement. **Rejected** (SCORING.md §2).
- **"Vacant space" marketing language:** strong hook, but factually indefensible given a bounded corpus and invites scientific/legal embarrassment. **Rejected.**
- **Quiet caveats only in footnotes:** user-facing emphasis belongs in the report body's scope disclosures; footnotes alone are insufficient. **Rejected** (FAILURE_HANDLING.md §10).

## Consequences

- **Positive:** scientifically defensible posture; avoids legal/IP-opinion liability; trustworthy differentiation recommendations ("appears less represented in the retrieved corpus", with evidence, uncertainty, and technical rationale — never guarantees); benchmark can enforce consistency (EVALUATION.md §8); users appraise coverage and decide for themselves.
- **Negative/costs:** marketing language is deliberately conservative; report framing must communicate value without overclaiming; some users expect a yes/no novelty answer and require UX education; guardrail implementation adds verification code and test burden.

## Related

ADR-0002 (evidence-first), SCORING.md, PRD.md §7 (non-goals), EVALUATION.md §8 (guardrails), FAILURE_HANDLING.md §10 (disclosure contracts), EVIDENCE_MODEL.md §6 (scope caveat).