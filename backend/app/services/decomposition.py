"""Deterministic idea decomposition (ARCHITECTURE.md M-3).

Without an AI provider configured, the system extracts plausible dimension
cues and high-frequency keywords deterministically. This is honest, auditable
signal extraction — never a claim-complete parse. An AI provider can replace
this stage later without changing the pipeline contract.
"""

import re
from collections import Counter

#: Cue words that associate idea tokens/bigrams with analysis dimensions.
_DIMENSION_CUES: dict[str, set[str]] = {
    "problem": {
        "problem", "challenge", "issue", "bottleneck", "limitation", "constraint",
        "expensive", "slow", "inefficient", "fragile", "difficulty", "gap",
    },
    "objective": {
        "objective", "goal", "aim", "purpose", "target", "improve", "reduce",
        "increase", "enable", "support", "achieve", "optimize",
    },
    "technology": {
        "framework", "platform", "tool", "library", "system", "engine", "stack",
        "model", "api", "language", "database", "protocol", "transformer",
        "neural", "blockchain", "kubernetes", "django", "react", "pytorch",
    },
    "method": {
        "method", "approach", "technique", "algorithm", "strategy", "pipeline",
        "heuristic", "procedure", "attention", "clustering", "forecasting",
        "retrieval", "reinforcement", "transfer",
    },
    "architecture": {
        "architecture", "design", "pattern", "layer", "modular", "monolithic",
        "distributed", "client-server", "microservices", "pipeline",
    },
    "dataset": {
        "dataset", "corpus", "benchmark", "data", "samples", "annotated",
        "imagery", "records", "logs",
    },
    "evaluation": {
        "evaluation", "metric", "accuracy", "latency", "precision", "recall",
        "f1", "throughput", "ablation", "benchmark", "test",
    },
}

_STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "with", "into", "from", "using",
    "that", "this", "these", "those", "which", "will", "can", "would", "should",
    "over", "under", "through", "between", "among", "our", "their", "its",
    "about", "such", "each", "also", "been", "was", "were", "have", "has",
}

_TOKEN_RE = re.compile(r"[a-z][a-z0-9\-]{1,}")


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences cleanly."""
    raw_sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [s.strip() for s in raw_sentences if len(s.strip()) > 8]


_GENERIC_MODIFIERS = {
    "technical", "scientific", "proposed", "novel", "new", "various", "general",
    "recent", "multiple", "several", "current", "existing", "different", "specific",
    "practical", "experimental", "key", "main", "important", "simple", "complex",
    "high", "low", "overall", "first", "second", "third", "primary", "paper", "study",
    "based", "approach", "method", "using", "presents", "presents a",
}

_TECHNICAL_STEMS = {
    "neural", "graph", "network", "agent", "reasoning", "learning", "verification",
    "transformer", "dynamics", "optimization", "mechanism", "model", "engine",
    "pipeline", "protocol", "quantum", "molecular", "equivariant", "geometric",
    "consensus", "privacy", "cryptography", "attention", "state", "space", "database",
    "kernel", "representation", "embedding", "encoder", "decoder", "heuristic",
    "hamiltonian", "invariant", "vector", "search", "indexer", "synthetic",
    "neurosymbolic", "knowledge", "multi-hop", "autonomous", "inference",
    "alignment", "benchmark", "distillation", "diffusion", "federated", "zero-knowledge",
}


def extract_technical_components(idea: str) -> list[str]:
    """Extract multi-word technical compounds rather than arbitrary adjacent word pairs.

    Filters out generic fragments like 'technical scientific' or 'proposed method' and
    isolates genuine conceptual units like 'neurosymbolic reasoning' or 'knowledge graphs'.
    """
    text_clean = re.sub(r"[^a-zA-Z0-9\-\s]", " ", idea.lower())
    raw_tokens = [w for w in text_clean.split() if w not in _STOPWORDS and len(w) >= 3]

    candidates: list[str] = []
    # 2-word compounds
    for i in range(len(raw_tokens) - 1):
        w1, w2 = raw_tokens[i], raw_tokens[i + 1]
        if w1 in _GENERIC_MODIFIERS or w2 in _GENERIC_MODIFIERS:
            continue
        if w1 == w2:
            continue
        # Check if either word matches technical cues
        has_tech = (
            w1 in _TECHNICAL_STEMS
            or w2 in _TECHNICAL_STEMS
            or any(
                cue in w1 or cue in w2
                for cue in _DIMENSION_CUES["technology"] | _DIMENSION_CUES["method"]
            )
        )
        if has_tech:
            candidates.append(f"{w1} {w2}")

    # 3-word technical compounds (e.g. 'equivariant graph neural networks')
    for i in range(len(raw_tokens) - 2):
        w1, w2, w3 = raw_tokens[i], raw_tokens[i + 1], raw_tokens[i + 2]
        if w1 in _GENERIC_MODIFIERS:
            continue
        has_tech = any(
            w in _TECHNICAL_STEMS or any(cue in w for cue in _DIMENSION_CUES["technology"])
            for w in (w1, w2, w3)
        )
        if has_tech and w1 != w2 and w2 != w3:
            candidates.append(f"{w1} {w2} {w3}")

    # Deduplicate preserving order
    seen: set[str] = set()
    filtered: list[str] = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            filtered.append(c)

    # If technical compounds were sparse, fall back to non-generic bigrams
    if len(filtered) < 2:
        for i in range(len(raw_tokens) - 1):
            w1, w2 = raw_tokens[i], raw_tokens[i + 1]
            if w1 not in _GENERIC_MODIFIERS and w2 not in _GENERIC_MODIFIERS and w1 != w2:
                phrase = f"{w1} {w2}"
                if phrase not in seen:
                    seen.add(phrase)
                    filtered.append(phrase)

    return filtered[:12]


def decompose(idea: str) -> dict:
    """Extract structured fields, keywords, bigrams, and per-dimension cues from the idea text."""
    text_lower = idea.lower().replace("\n", " ")
    tokens = _TOKEN_RE.findall(text_lower)
    tokens = [t for t in tokens if t not in _STOPWORDS and len(t) > 2]

    bigrams: list[str] = []
    for index in range(len(tokens) - 1):
        first, second = tokens[index], tokens[index + 1]
        if first in _STOPWORDS or second in _STOPWORDS or first == second:
            continue
        bigrams.append(f"{first} {second}")

    freq = Counter(bigrams + tokens)
    keywords = [k for k, _count in freq.most_common(24)]

    dimension_terms: dict[str, list[str]] = {}
    for dimension, cues in _DIMENSION_CUES.items():
        matches = [k for k in keywords if k in cues or any(cue in k for cue in cues)]
        if matches:
            dimension_terms[dimension] = matches[:6]

    # Meaningful technical component extraction
    concepts = extract_technical_components(idea)

    # Sentence-based structured extraction
    sentences = _split_sentences(idea)

    # 1. Problem
    problem_sentences = [
        s for s in sentences
        if any(w in s.lower() for w in _DIMENSION_CUES["problem"])
    ]
    problem = (
        problem_sentences[0]
        if problem_sentences
        else (
            sentences[0]
            if sentences
            else "Challenge or bottleneck addressed by the technical idea."
        )
    )

    # 2. Objective
    objective_cues = _DIMENSION_CUES["objective"] | {"propose", "proposes", "build", "develop"}
    objective_sentences = [
        s for s in sentences
        if any(w in s.lower() for w in objective_cues)
    ]
    objective = (
        objective_sentences[0]
        if objective_sentences
        else (
            sentences[1]
            if len(sentences) > 1
            else "Primary engineering objective or target outcome."
        )
    )

    # 3. Technologies
    known_tech = {
        "python", "fastapi", "react", "next.js", "pytorch",
        "tensorflow", "redis", "postgresql", "docker", "llm", "transformer",
    }
    detected_techs = [
        k for k in keywords
        if any(cue in k for cue in _DIMENSION_CUES["technology"])
        or k in known_tech
    ]
    technologies = list(dict.fromkeys(detected_techs))[:8]
    if not technologies:
        technologies = [k for k in keywords if len(k) > 4][:4]

    # 4. Methods
    detected_methods = [
        k for k in (bigrams + keywords)
        if any(cue in k for cue in _DIMENSION_CUES["method"])
    ]
    methods = list(dict.fromkeys(detected_methods))[:8]
    if not methods:
        method_cues = ("system", "pipeline", "model", "analysis")
        methods = [b for b in bigrams if any(cue in b for cue in method_cues)][:4]

    # 5. Datasets
    detected_datasets = [
        k for k in (bigrams + keywords)
        if any(cue in k for cue in _DIMENSION_CUES["dataset"])
    ]
    datasets = list(dict.fromkeys(detected_datasets))[:6]

    # 6. Architecture
    arch_sentences = [
        s for s in sentences
        if any(w in s.lower() for w in _DIMENSION_CUES["architecture"])
    ]
    architecture = (
        arch_sentences[0]
        if arch_sentences
        else "Modular pipeline coordinating decomposition, retrieval, evidence, and synthesis."
    )

    # 7. Claims
    claims: list[str] = []
    claim_markers = (
        "improve", "reduces", "enables", "achieves",
        "outperforms", "ensures", "supports", "provides",
    )
    for s in sentences:
        if any(m in s.lower() for m in claim_markers) and len(s) < 240:
            claims.append(s)
    if not claims and sentences:
        claims = [f"Hypothesis: {sentences[0][:180]}"]
    claims = claims[:5]

    # 8. Research questions
    rqs: list[str] = [s for s in sentences if s.endswith("?")]
    if not rqs:
        primary_tech = technologies[0] if technologies else "proposed method"
        primary_obj = (dimension_terms.get("objective") or ["system behavior"])[0]
        rqs = [
            f"Under what conditions does {primary_tech} improve {primary_obj}?",
            "What trade-offs emerge between latency, cost, and reliability in this architecture?",
            "How robust is the approach across varying data distributions and noise levels?",
        ]

    return {
        "problem": problem,
        "objective": objective,
        "technologies": technologies,
        "methods": methods,
        "datasets": datasets,
        "architecture": architecture,
        "claims": claims,
        "research_questions": rqs,
        "keywords": keywords,
        "bigrams": [b for b in bigrams],
        "dimensions": dimension_terms,
        "concepts": concepts,
        "technical_components": concepts,
    }


def decision_signal(idea: str) -> int:
    """Deterministic UI-only indicator; explicitly not a novelty score.

    Mirrors the Manus demo semantics so existing clients stay stable: a stable
    function of the normalized idea text in the 55–85 range.
    """
    normalized = "".join(ch for ch in idea.lower() if ch.isalnum())
    return 55 + (sum(ord(ch) for ch in normalized) % 31)