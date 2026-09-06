"""Query planning (ARCHITECTURE.md M-4 & RESEARCH QUALITY §2.1).

Generates high-signal, technically grounded retrieval queries prioritized by:
- Technology stack & primitives
- Methodological strategy & algorithms
- System architecture & pipeline topology
- Empirical datasets & evaluation benchmarks
- Concrete domain bottleneck / problem formulation
- Technical component combinations
Avoids low-information single-word fragments and generic stopwords.
"""

from app.services.decomposition import decompose


def plan_queries(idea: str) -> list[dict]:
    """Build high-signal retrieval queries across technical dimensions."""
    decomposition = decompose(idea)
    queries: list[dict] = []
    seen_texts: set[str] = set()

    def add_query(text: str, purpose: str, ordering: int) -> None:
        clean = " ".join(text.strip().split())
        if len(clean) > 280:
            clean = clean[:280]
        if clean and clean.lower() not in seen_texts:
            seen_texts.add(clean.lower())
            queries.append({"query_text": clean, "purpose": purpose, "ordering": ordering})

    # 1. Core query: the concise technical hypothesis/objective
    objective = decomposition.get("objective", "")
    technologies = decomposition.get("technologies") or []
    methods = decomposition.get("methods") or []
    concepts = decomposition.get("concepts") or []
    datasets = decomposition.get("datasets") or []

    core_parts: list[str] = []
    if technologies:
        core_parts.append(technologies[0])
    if methods:
        core_parts.append(methods[0])
    if objective and len(objective) < 140:
        core_parts.append(objective)
    core_text = " ".join(core_parts) if core_parts else idea.strip()[:200]
    add_query(core_text, "core", 0)

    # 2. Technology query: prioritized technology primitives
    if technologies:
        tech_query = " ".join(technologies[:3])
        add_query(tech_query, "technology", len(queries))

    # 3. Method query: algorithmic mechanisms
    if methods:
        method_query = f"{' '.join(methods[:2])} technique algorithm"
        add_query(method_query, "method", len(queries))

    # 4. Problem & domain query
    problem = decomposition.get("problem", "")
    if problem and len(problem) > 10:
        # Extract meaningful problem focus
        problem_snippet = problem.split(".")[0] if "." in problem else problem[:120]
        add_query(problem_snippet, "problem", len(queries))

    # 5. Dataset & benchmark query
    if datasets:
        dataset_query = f"{' '.join(datasets[:2])} benchmark dataset"
        add_query(dataset_query, "dataset", len(queries))
    elif technologies:
        add_query(f"{technologies[0]} benchmark evaluation dataset", "dataset", len(queries))

    # 6. Architecture & pipeline query
    architecture = decomposition.get("architecture", "")
    if architecture and len(architecture) < 140:
        add_query(architecture, "architecture", len(queries))

    # 7. Multi-component combination query (for collision analysis grounding)
    if len(concepts) >= 2:
        combination_query = f'"{concepts[0]}" AND "{concepts[1]}"'
        add_query(combination_query, "combination", len(queries))

    return queries