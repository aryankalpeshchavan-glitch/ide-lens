# ADR-0006: Research Graph in PostgreSQL

**Status:** Accepted (M0 decision). **Date:** 2026-09-01 (M0).

## Context

ARCHITECTURE.md M-9 defines a research/evidence graph: nodes (sources, evidence, claims, technologies, methods, datasets) with typed edges (used_by, contradicts, similar_to, addresses_problem, implements_method), used by contradiction detection, similarity, collision analysis, and traceability. A dedicated graph database (e.g., Neo4j) would add a new storage system, new operational burden, and cross-system consistency concerns to a single-project modular monolith (ADR-0001).

## Decision

Represent the initial Research Graph using **PostgreSQL relational data**. Nodes are the existing entity tables (SourceItem, Evidence, Claim, Technology, Method, Dataset); typed edges are stored relationally (e.g., an `EvidenceGraphEdge` table carrying edge_type, weight/confidence, and provenance) or as junction tables. No dedicated graph database is introduced initially. Traversal is kept shallow; if graph-depth queries later prove expensive, add targeted denormalization, caching, or a graph store — reconsidered via a new ADR only when measured need justifies it.

## Alternatives considered

- **Dedicated graph database (e.g., Neo4j):** first-class graph queries, but adds an extra system, data duplication/sync, and operational complexity at a stage where graph queries are shallow and traceability-centric. **Deferred** unless measurements justify it.
- **JSONB adjacency on a single table:** simple for small graphs, but weak for typed edges with provenance and for referential integrity; a relational edge table fits better.
- **No explicit edges (implicit joins only):** loses typed-edge semantics (edge type, weight, provenance) that contradiction/similarity/collision logic requires. **Rejected.**

## Consequences

- **Positive:** one system of record; transactional consistency between nodes and edges; traceability chains stay enforceable with foreign keys; simpler operations and observability (ADR-0001).
- **Negative/costs:** deep multi-hop graph queries are less ergonomic than a graph database; mitigated by keeping traversals shallow and benchmarking before optimizing. Revisit with a new ADR if graph workloads justify it.

## Related

ADR-0001, ADR-0002, ARCHITECTURE.md §2 (M-9), DATA_MODEL.md §2 (EvidenceGraphEdge).