"""Research coverage (SCORING.md §9).

Per-dimension evidence sufficiency within the retrieved and analysed corpus:
strong / moderate / limited / insufficient. Never a novelty or global
completeness statement.
"""


def _bucket(count: int, source_count: int) -> str:
    if count == 0:
        return "insufficient"
    if count >= 5 and source_count >= 3:
        return "strong"
    if count >= 2 and source_count >= 2:
        return "moderate"
    return "limited"


def compute_coverage(evidences: list[dict], source_adapter_counts: dict) -> list[dict]:
    """Compute per-dimension coverage.

    ``evidences`` entries: ``{"id", "dimension", "source_item_id",
    "adapter_id" (optional), "strength"}``.
    """
    by_dimension: dict[str, list[dict]] = {}
    for evidence in evidences:
        dimension = evidence.get("dimension") or "other"
        by_dimension.setdefault(dimension, []).append(evidence)

    results: list[dict] = []
    for dimension, items in sorted(by_dimension.items()):
        source_ids = {e.get("source_item_id") for e in items if e.get("source_item_id")}
        source_count = len(source_ids)
        level = _bucket(len(items), source_count)
        confidence = "high" if source_count >= 3 else ("medium" if source_count >= 2 else "low")
        results.append(
            {
                "dimension": dimension,
                "level": level,
                "explanation": (
                    f"{len(items)} deduplicated item(s) from {source_count} source(s) "
                    f"bear on the '{dimension}' dimension within the retrieved and "
                    "analysed corpus."
                ),
                "evidence_count": len(items),
                "source_count": source_count,
                "confidence": confidence,
            }
        )
    return results