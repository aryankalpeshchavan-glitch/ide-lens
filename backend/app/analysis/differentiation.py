"""Differentiation engine (ARCHITECTURE.md M-14).

Produces evidence-grounded recommendations with overlap disclosure, hypotheses,
supporting evidence, and mandatory uncertainty statements. Never implies
novelty or freedom-to-operate.
"""


def compute_differentiation(
    similarity_results: list[dict],
    gap_results: list[dict],
    collision_results: list[dict],
) -> list[dict]:
    """Build the differentiation recommendation record."""
    ranked = sorted(
        (s for s in similarity_results if s.get("score") is not None),
        key=lambda s: s["score"],
        reverse=True,
    )
    best = ranked[0] if ranked else None

    if best is not None:
        overlap_summary = (
            f"Strongest overlap is on the '{best['dimension']}' dimension "
            f"(score {best['score']:.2f}, {best['confidence']} confidence). "
            "This measures resemblance within the retrieved corpus; it is not a "
            "plagiarism or infringement judgment."
        )
        overlap_evidence_ids = list(best.get("evidence_ids") or [])
    else:
        overlap_summary = "No strong per-dimension overlap signals were produced."
        overlap_evidence_ids = []

    less_represented = next(
        (
            gap
            for gap in gap_results
            if gap.get("saturation_bucket") in ("limited_evidence_found", "insufficient_evidence")
        ),
        None,
    )
    top_collision = next(
        (
            collision
            for collision in collision_results
            if collision.get("level") in ("limited_evidence_found", "insufficient_evidence")
        ),
        None,
    )

    supporting_evidence_ids: list[str] = []
    if less_represented is not None:
        subject = less_represented.get("subject") or {}
        if less_represented.get("scope_kind") == "dimension":
            area = f"the '{subject.get('dimension', '')}' dimension"
        else:
            area = f"the {subject.get('components', [])} combination"
        less_represented_area = (
            f"{area} is comparatively less represented within the retrieved corpus."
        )
        supporting_evidence_ids = [
            str(item)
            for item in (less_represented.get("evidence_basis") or {}).get(
                "evidence_ids", []
            )
        ]
    elif top_collision is not None:
        less_represented_area = (
            f"The {top_collision.get('component_ids')} combination is comparatively "
            "less represented within the retrieved corpus."
        )
    else:
        less_represented_area = (
            "No comparatively less-represented area emerged from the retrieved corpus."
        )

    return [
        {
            "overlap_summary": overlap_summary,
            "overlap_evidence_ids": overlap_evidence_ids,
            "differentiation_hypothesis": (
                "A tightly scoped contribution in the described area, implemented with a "
                "disciplined evaluation protocol, is a defensible differentiation direction."
            ),
            "rationale": (
                "Overlap signals crowd the risky dimensions, while comparatively "
                "less-represented combinations leave more room for a defensible, "
                "measurable contribution."
            ),
            "less_represented_area": less_represented_area,
            "supporting_evidence_ids": supporting_evidence_ids,
            "remaining_uncertainty": (
                "These signals are corpus-dependent and do not establish novelty, "
                "absence of prior work, or freedom to operate."
            ),
        }
    ]

