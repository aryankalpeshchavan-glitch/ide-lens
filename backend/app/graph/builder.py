"""Research/evidence graph construction (ADR-0006).

Builds run-scoped nodes and typed edges that resolve back to source and
evidence identifiers. Persisted relationally via the ORM.
"""


def build_graph(
    *,
    idea: str,
    sources: list[dict],
    evidences: list[dict],
    dimensions: list[str],
) -> tuple[list[dict], list[dict]]:
    """Return (nodes, edges) for the run's research graph."""
    nodes: list[dict] = []
    edges: list[dict] = []

    idea_node = {
        "id": "idea",
        "node_type": "idea",
        "label": idea[:80],
        "reference_id": None,
    }
    nodes.append(idea_node)

    dimension_nodes = {}
    for dimension in dimensions:
        dimension_nodes[dimension] = {
            "id": f"dim:{dimension}",
            "node_type": "dimension",
            "label": dimension,
            "reference_id": None,
        }
        nodes.append(dimension_nodes[dimension])
        edges.append(
            {
                "source_node_id": "idea",
                "target_node_id": f"dim:{dimension}",
                "relationship_type": "addresses",
                "weight": 1.0,
                "confidence": "high",
            }
        )

    evidence_by_id: dict[str, dict] = {}
    for evidence in evidences:
        node_id = f"ev:{evidence['id']}"
        evidence_by_id[str(evidence["id"])] = node_id
        nodes.append(
            {
                "id": node_id,
                "node_type": "evidence",
                "label": f"evidence/{evidence.get('dimension', 'other')}",
                "reference_id": evidence["id"],
            }
        )
        edges.append(
            {
                "source_node_id": f"src:{evidence['source_item_id']}",
                "target_node_id": node_id,
                "relationship_type": "has_evidence",
                "weight": _strength_weight(evidence.get("strength", "moderate")),
                "confidence": evidence.get("extraction_confidence", "medium"),
            }
        )
        dimension = evidence.get("dimension")
        if dimension in dimension_nodes:
            edges.append(
                {
                    "source_node_id": node_id,
                    "target_node_id": f"dim:{dimension}",
                    "relationship_type": "relates_to",
                    "weight": 0.7,
                    "confidence": "medium",
                }
            )

    for source in sources:
        node_id = f"src:{source['id']}"
        nodes.append(
            {
                "id": node_id,
                "node_type": "source",
                "label": (source.get("title") or "source")[:80],
                "reference_id": source["id"],
            }
        )
    return nodes, edges


def _strength_weight(strength: str) -> float:
    return {"strong": 1.0, "moderate": 0.6, "weak": 0.3}.get(strength, 0.5)