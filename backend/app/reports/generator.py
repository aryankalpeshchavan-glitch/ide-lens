"""Report generation (ARCHITECTURE.md M-15, ADR-0005).

Deterministic templated assembly of persisted artifacts with strict language
``guardrails`` (EVALUATION.md §8). The rendered report always discloses scope:
queries, sources, per-dimension coverage, failures, and the corpus caveat.
"""

from datetime import UTC, datetime

BANNED_PHRASES = [
    "100% novel",
    "100 percent novel",
    "first-ever",
    "first ever",
    "no prior work",
    "nobody has done this",
    "no one has done this",
    "vacant space",
    "unexplored space",
    "proves novelty",
    "proven novel",
    "guarantee of novelty",
    "objective truth",
]


class LanguageGuardrailError(RuntimeError):
    """Raised when proposed report text violates the banned-phrase policy."""


def check_language(text: str) -> list[str]:
    """Return the banned-phrase violations found in ``text`` (empty = pass)."""
    lowered = text.lower()
    return [phrase for phrase in BANNED_PHRASES if phrase in lowered]


def render_report(
    *,
    idea: str,
    sources: list[dict],
    evidences: list[dict],
    similarity_results: list[dict],
    coverage_results: list[dict],
    contradictions: list[dict],
    gaps: list[dict],
    collisions: list[dict],
    stress_tests: list[dict],
    differentiations: list[dict],
    queries: list[dict],
    disclosure: dict,
) -> tuple[str, list[dict]]:
    """Render the markdown report plus a citations map (evidence -> source)."""
    citations = build_citations(evidences, sources)

    lines: list[str] = [
        "# IdeaLens Research Report",
        "",
        f"*Generated {datetime.now(UTC).isoformat()} · scope-aware · not an originality verdict*",
        "",
        "## 1. Idea",
        f"> {idea}",
        "",
        "## 2. Research scope",
        f"- Queries planned: {disclosure.get('queries_planned', 0)}",
        f"- Queries executed: {disclosure.get('queries_executed', 0)}",
        f"- Sources retrieved (deduplicated): {len(sources)}",
        f"- Evidence records: {len(evidences)}",
        "- Caveat: the retrieved corpus is not the whole field.",
        "",
        "## 3. Per-dimension research coverage",
    ]
    for coverage in coverage_results:
        lines.append(
            f"- **{coverage['dimension']}**: {coverage['level']} "
            f"({coverage['evidence_count']} items, {coverage['source_count']} sources) — "
            f"{coverage['explanation']}"
        )
    lines.extend(["", "## 4. Multidimensional similarity"])
    for item in similarity_results:
        evidence_refs = "n/a" if not item.get("evidence_ids") else ", ".join(
            str(x)[:8] for x in item["evidence_ids"][:5]
        )
        lines.append(
            f"- {item['dimension']}: {item['score']:.2f} "
            f"(confidence {item['confidence']}; evidence {evidence_refs}). "
            f"{item['explanation']}"
        )
    lines.extend(["", "## 5. Contradictions"])
    for contradiction in contradictions:
        lines.append(
            f"- **{contradiction['subject']}** — {contradiction['conflict_summary']}"
            f" (comparability: {contradiction['comparability']})"
        )
    lines.extend(["", "## 6. Research gaps"])
    for gap in gaps:
        lines.append(f"- **{gap['saturation_bucket']}**: {gap['standardized_language']}")
    lines.extend(["", "## 7. Idea collisions"])
    for collision in collisions:
        lines.append(
            f"- {collision['component_ids']}: {collision['level']} "
            f"({collision.get('evidence_count', 0)} items)"
        )
    lines.extend(["", "## 8. Stress test"])
    for stress in stress_tests:
        lines.append(f"- **{stress['category']}**: {stress['severity']} — {stress['explanation']}")
    lines.extend(["", "## 9. Differentiation"])
    for differentiation in differentiations:
        lines.append(f"- Overlap: {differentiation['overlap_summary']}")
        lines.append(f"- Less represented: {differentiation['less_represented_area']}")
        lines.append(f"- Uncertainty: {differentiation['remaining_uncertainty']}")
    lines.extend(["", "## 10. References"])
    for citation in citations:
        lines.append(
            f"- {citation['title']} — {citation.get('url') or citation['identifiers']}"
        )
    lines.extend(
        [
            "",
            "## Scope caveat",
            "This report reflects the retrieved and analysed corpus only. It is not a statement "
            "of novelty, a plagiarism finding, or freedom-to-operate advice.",
        ]
    )

    joined = "\n".join(lines)
    violations = check_language(joined)
    if violations:
        raise LanguageGuardrailError(f"Banned phrasing detected: {violations}")
    return joined, citations


def build_citations(evidences: list[dict], sources: list[dict]) -> list[dict]:
    """Map each evidence to its source title/url for the reference section."""
    by_id = {str(source["id"]): source for source in sources}
    citations = []
    for evidence in evidences:
        source = by_id.get(str(evidence.get("source_item_id"))) or {}
        identifiers = source.get("identifiers") or {}
        stable = (
            identifiers.get("doi") or identifiers.get("arxiv_id") or identifiers.get("github_repo")
        )
        citations.append(
            {
                "evidence_id": str(evidence["id"]),
                "title": source.get("title") or "(unknown title)",
                "url": source.get("primary_url"),
                "identifiers": stable,
            }
        )
    return citations
