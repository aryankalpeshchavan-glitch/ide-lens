# IdeaLens

IdeaLens is an **evidence-driven technical idea intelligence engine**. A user submits a technical/research/project idea — as plain text or a TXT/PDF/DOCX document — and IdeaLens investigates the existing technical landscape across academic and open-source sources, then produces an evidence-grounded analysis covering: the problems the idea addresses; existing approaches; technologies and methods already used; datasets already used; existing research; existing open-source implementations; existing practical/commercial solutions where appropriate; overlap between the proposed idea and discovered work; contradictions in the discovered evidence; areas with dense existing work; areas where evidence is comparatively limited; possible combinations of technologies or components that appear less represented; and defensible ways to differentiate the proposed project.

> **Status: Milestone 0 (M0) documentation complete; Milestone 1 (M1) engineering foundation established.** A runnable FastAPI backend skeleton now exists with configuration, database/Redis infrastructure boundaries, `/health`, tests, and linting. No product intelligence (parsing, retrieval, evidence, analysis, workers) is implemented yet. The Next.js scaffold was generated for the future frontend but is intentionally not customized in M1.

## Core principles

- **Evidence-first** — every important analytical conclusion traces back to evidence, then to a source, then to the original source identifier/URL. See [ADR-0002](docs/ADR/0002-evidence-first-architecture.md).
- **The LLM is not the whole system** — AI handles interpretation and extraction; deterministic code handles validation, normalization, deduplication, data integrity, scoring calculations where possible, and evidence linkage.
- **Multidimensional similarity** — similarity is reported per dimension (problem, objective, technology, method, architecture, dataset, domain/application) with explanation — never a single "novelty score". See [docs/SCORING.md](docs/SCORING.md).
- **No novelty guarantees** — IdeaLens never claims an idea is "100% novel", never treats limited retrieved evidence as proof of novelty, and never treats similarity as plagiarism or IP infringement. See [ADR-0005](docs/ADR/0005-no-novelty-guarantees.md).
- **Reproducible research runs** — inputs, generated queries, sources, evidence, analysis results, scoring configuration, model/provider information, errors, and partial failures are persisted per run.
- **Research Coverage** — the report communicates per-dimension evidence sufficiency (strong / moderate / limited / insufficient) for the idea's dimensions — never as novelty or global completeness. See [docs/SCORING.md](docs/SCORING.md) §9.

## Documentation

| Doc | Purpose |
|---|---|
| [docs/PRD.md](docs/PRD.md) | Product vision, problem statement, target users, use cases, core features, MVP, non-goals, success criteria, risks |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture, major modules, request/data flow, research-run lifecycle, source adapter architecture, AI/embedding abstractions, evidence flow, failure boundaries, deployment concept |
| [docs/DATA_MODEL.md](docs/DATA_MODEL.md) | Major entities and relationships (conceptual; no migrations yet) |
| [docs/EVIDENCE_MODEL.md](docs/EVIDENCE_MODEL.md) | Evidence, source, claim, claim–evidence linkage, provenance, confidence, retrieval metadata, traceability |
| [docs/SCORING.md](docs/SCORING.md) | Scoring philosophy: multidimensional similarity, evidence strength, source ranking, research saturation, research coverage, gap signals |
| [docs/SOURCE_POLICY.md](docs/SOURCE_POLICY.md) | Allowed sources, API-first access, rate limiting, caching, attribution, metadata handling, copyright, failure behavior, privacy |
| [docs/EVALUATION.md](docs/EVALUATION.md) | Benchmark philosophy, structure, datasets, metrics, future human evaluation (benchmark NOT created in M0) |
| [docs/FAILURE_HANDLING.md](docs/FAILURE_HANDLING.md) | Retry policy, timeouts, rate-limit handling, partial-source failure, malformed data, AI failure, worker failure, observability |
| [docs/ADR/](docs/ADR/) | Architectural decision records 0001–0006 |

## Decided technology stack

| Layer | Choice |
|---|---|
| Backend | Python · FastAPI · Pydantic · SQLAlchemy |
| Database | PostgreSQL |
| Background processing | Redis queue + background workers |
| Frontend | Next.js · TypeScript · Tailwind CSS |
| Deployment | Modular monolith (conceptual; no infra configured yet) |

## Repository layout

```
README.md
backend/            M1: FastAPI backend skeleton (see backend/README.md)
docs/
  PRD.md
  ARCHITECTURE.md
  DATA_MODEL.md
  EVIDENCE_MODEL.md
  SCORING.md
  SOURCE_POLICY.md
  EVALUATION.md
  FAILURE_HANDLING.md
  ADR/
    0001-modular-monolith.md
    0002-evidence-first-architecture.md
    0003-asynchronous-research-runs.md
    0004-source-adapter-architecture.md
    0005-no-novelty-guarantees.md
    0006-research-graph-in-postgresql.md
frontend/           Scaffolded with create-next-app (not customized in M1)
```

## Milestones

- **M0** — project specification and architecture documentation. *Complete.*
- **M1** — engineering foundation: runnable FastAPI backend with `GET /health`, environment configuration, SQLAlchemy/Redis infrastructure boundaries, pytest + Ruff. *Backend established; frontend scaffold generated but not customized.*
- **M2+** — product functionality (parsing, retrieval, evidence, analysis, reports, background workers) per the architecture documentation.

## M1 local setup (backend)

Prerequisites: Python 3.11+ (tested on 3.14). PostgreSQL and Redis are **not**
required to run the backend; `/health` reports them as `unavailable` until they
are reachable.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

Configure environment variables by copying `backend/.env.example` to
`backend/.env` and adjusting values. All variables have defaults; a `.env` file
is optional for local boot.

```powershell
Copy-Item .env.example .env   # then edit as needed
```

Start the backend:

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```

Check it:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Run tests and lint:

```powershell
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m ruff check .
```

### `/health` contract

Process health and dependency health are reported separately and never
inferred from each other. `status` reflects the API process; `dependencies`
reflects real probes (unavailable dependencies are reported as `unavailable`,
not as healthy).

## M1 scope

- FastAPI application with `GET /health`.
- Environment configuration via `backend/.env.example` (PostgreSQL, Redis, CORS, environment mode).
- SQLAlchemy engine/session configuration for PostgreSQL (no entities, no tables, no migrations yet).
- Redis configuration boundary (no queues, clients, or workers yet).
- pytest test suite for `/health`; Ruff linting.

Not implemented in M1 (intentionally): document parsing and ingestion, idea
decomposition, query generation, source adapters (Semantic Scholar, Crossref,
arXiv, GitHub), retrieval, deduplication, embeddings, similarity, evidence
extraction, research graph, contradiction/gap/collision analysis,
differentiation, report generation, authentication, user management,
background research workers, database migrations, and production deployment.
Corresponding backend packages exist as clearly marked architectural
boundaries only.

## M1 non-goals

The M0 milestone was documentation-only. M1 intentionally still does **not**
implement any product functionality: no Docker/container configuration, no
CI/CD, no database migrations, no API keys, no source adapters or external API
integrations, no embedding or LLM calls, no background workers, no
authentication, and no fake test results. The product-level non-goals are in
[docs/PRD.md](docs/PRD.md).