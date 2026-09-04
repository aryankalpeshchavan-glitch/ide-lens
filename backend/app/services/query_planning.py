"""Query planning (ARCHITECTURE.md M-4).

Queries are generated from the decomposition deterministically so runs are
reproducible. Each planned query records its purpose (dimension/angle) and is
persisted per run.
"""

from app.services.decomposition import decompose


def plan_queries(idea: str) -> list[dict]:
    """Build retrieval queries: a core query plus one per detected dimension."""
    decomposition = decompose(idea)
    queries: list[dict] = []

    core = idea.strip().replace("\n", " ")
    if len(core) > 300:
        core = core[:300]
    queries.append({"query_text": core, "purpose": "core", "ordering": 0})

    dimension_terms = decomposition["dimensions"]
    for index, (dimension, terms) in enumerate(dimension_terms.items(), start=1):
        if not terms:
            continue
        query_text = " ".join(terms[:4])
        queries.append(
            {"query_text": query_text, "purpose": dimension, "ordering": index}
        )

    concepts = decomposition.get("concepts") or []
    if len(concepts) >= 2:
        combination = " AND ".join(concepts[:3])
        queries.append(
            {"query_text": combination, "purpose": "combination", "ordering": len(queries)}
        )

    return queries