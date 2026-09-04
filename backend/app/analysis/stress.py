"""Idea stress test (ARCHITECTURE.md M-13).

Deterministic inventory of risks: research saturation, dataset availability,
evaluation difficulty, unsupported assumptions, and evidence weaknesses.
LLM-supported synthesis can extend these later; the deterministic baseline is
evidence-referenced and conservative.
"""

import re

from app.analysis.common import score_band

_ASSUMPTION_MARKERS = re.compile(
    r"\b(should|could|will|enables|allows|would|just|simply|only needs)\b", re.IGNORECASE
)


def compute_stress(
    idea: str,
    similarity_results: list[dict],
    coverage_results: list[dict],
    *,
    evidence_count: int,
) -> list[dict]:
    results: list[dict] = []

    best_similarity = max(
        (s for s in similarity_results if s.get("score") is not None),
        key=lambda s: s["score"],
        default=None,
    )
    if best_similarity is not None:
        if best_similarity["score"] >= 0.6:
            severity = "high"
        elif best_similarity["score"] >= 0.4:
            severity = "medium"
        else:
            severity = "low"
        results.append(
            {
                "category": "research_saturation",
                "severity": severity,
                "explanation": (
                    f"The '{best_similarity['dimension']}' dimension shows a "
                    f"{score_band(best_similarity['score'])} similarity band across "
                    f"{len(best_similarity.get('evidence_ids') or [])} retrieved item(s). "
                    "Strong overlap signals suggest crowding in that dimension."
                ),
                "evidence_ids": best_similarity.get("evidence_ids") or [],
                "recommendation": (
                    "Narrow the differentiator to the exact mechanism and evaluation protocol."
                ),
            }
        )

    dataset_coverage = _coverage_for(coverage_results, "dataset")
    if dataset_coverage is not None:
        severity = (
            "medium"
            if dataset_coverage["level"] in ("strong", "moderate", "limited")
            else "low"
        )
        results.append(
            {
                "category": "dataset_availability",
                "severity": severity,
                "explanation": (
                    f"Dataset evidence within the retrieved corpus is "
                    f"'{dataset_coverage['level']}'."
                ),
                "evidence_ids": [],
                "recommendation": (
                    "Lock a benchmark suite and report harmonization steps before "
                    "comparing results."
                ),
            }
        )

    evaluation_coverage = _coverage_for(coverage_results, "evaluation")
    if evaluation_coverage is not None:
        severity = "high" if evaluation_coverage["level"] in ("strong", "moderate") else "medium"
        results.append(
            {
                "category": "evaluation_difficulty",
                "severity": severity,
                "explanation": (
                    f"Evaluation evidence is '{evaluation_coverage['level']}' in the "
                    "retrieved corpus; protocol choices materially affect conclusions."
                ),
                "evidence_ids": [],
                "recommendation": "Publish protocol, splits, and ablations.",
            }
        )

    if _ASSUMPTION_MARKERS.search(idea):
        results.append(
            {
                "category": "unsupported_assumptions",
                "severity": "medium",
                "explanation": (
                    "The idea text contains hedged or assumed language (e.g. 'should', "
                    "'will', 'enables'); those assumptions are not evidence-backed."
                ),
                "evidence_ids": [],
                "recommendation": "List assumptions explicitly and de-risk them first.",
            }
        )

    if evidence_count < 5:
        results.append(
            {
                "category": "evidence_weaknesses",
                "severity": "medium" if evidence_count else "high",
                "explanation": (
                    f"Only {evidence_count} evidence record(s) were produced; coverage is thin."
                ),
                "evidence_ids": [],
                "recommendation": "Widen query diversity and source coverage before conclusions.",
            }
        )

    return results


def _coverage_for(coverage_results: list[dict], dimension: str) -> dict | None:
    for coverage in coverage_results:
        if coverage.get("dimension") == dimension:
            return coverage
    return None