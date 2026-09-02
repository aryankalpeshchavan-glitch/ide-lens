# ADR-0001: Modular Monolith

**Status:** Accepted (M0 decision). **Date:** 2026-09-01 (M0).

## Context

IdeaLens is a new, evidence-driven idea-intelligence product with an asynchronous research pipeline spanning retrieval from multiple sources, evidence extraction, similarity/gap/contradiction analysis, and report generation. The pipeline needs persistence (PostgreSQL), background work (Redis + workers), external API fan-out, LLM/embedding providers, and a Next.js frontend.

We are starting a production-oriented portfolio project with a small team, evolving requirements, and a need to ship value quickly while keeping the system understandable, observable, and easy to change.

Options considered: microservices, Kubernetes with a service mesh, orchestration/autonomous-agent platforms, and a monolithic application with two process types (API + worker).

## Decision

Use a **modular monolith**:

- One backend codebase (Python/FastAPI) containing clearly separated modules: API layer; domain services (ingestion, decomposition, claims, query planning, retrieval orchestration, evidence, analysis, report); source adapters; AI and embedding abstractions; and the worker entrypoint.
- Two deployable process types run from the same codebase: `api` (FastAPI, serves HTTP) and `worker` (consumes the Redis queue and executes research-run stages).
- PostgreSQL is the system of record; Redis is the queue, cache, and rate-limit/retry bookkeeping; Next.js/TypeScript frontend calls the API over JSON.
- No Kubernetes, no microservices, no service mesh, no unnecessary distributed infrastructure, and no giant autonomous-agent frameworks (see also ADR-0002).

## Alternatives considered

- **Microservices (one service per pipeline stage):** clear stage isolation in theory, but high operational complexity (many deploys, monitoring), cross-service data-consistency cost, and churn while pipeline semantics are still evolving. **Rejected for now**; cheap to migrate later if warranted.
- **Kubernetes + service mesh:** heavyweight operations for a single-project portfolio; contradicts the simplicity principle. **Rejected.**
- **Agentic orchestration platform:** autonomous-agent loops conflict with the requirement that the LLM is not the entire system and that deterministic control validates, normalizes, and extracts deterministically. **Rejected** (see ADR-0002).
- **Pure single process with in-process async jobs:** simpler operations, but producer/consumer lifecycle, retries, visibility timeouts, durability across restarts, and backpressure remain manual; the Redis queue architecture is already decided (ADR-0003). Two process types from one codebase balance simplicity and clarity. **Selected.**

## Consequences

- **Positive:** simpler operations (one repo/image, common logging and observability); data consistency within a single database transaction scope where needed; new source adapters can be added without re-architecting; small-team efficiency; easier code review and onboarding.
- **Negative/risks:** scaling must be handled deliberately for two process types (API vs. worker replicas); in-process coupling can tempt module-boundary violations — mitigated by module interfaces (adapter/AI/embedding contracts) and ADRs; a future split to services is possible but requires disciplined seams.

## Related

ADR-0002 (evidence-first), ADR-0003 (async runs), ADR-0004 (source adapters), ARCHITECTURE.md §1 and §10.