# IdeaLens

> **An evidence-driven technical idea intelligence engine.**

IdeaLens decomposes technical, scientific, and software ideas, plans multi-angle queries across academic literature and open-source repositories, extracts provenance-tracked evidence, computes multidimensional similarity, and generates structured analytical signals (coverage, contradictions, research gaps, idea collisions, stress testing, and defensible differentiation) with rigorous scientific integrity guardrails.

---

## Table of Contents

- [1. Problem Being Solved](#1-problem-being-solved)
- [2. What IdeaLens Does](#2-what-idealens-does)
- [3. Core Research Workflow](#3-core-research-workflow)
- [4. High-Level Architecture](#4-high-level-architecture)
- [5. Technology Stack](#5-technology-stack)
- [6. Database & Persistence Layer](#6-database--persistence-layer)
- [7. Redis & Background Worker Model](#7-redis--background-worker-model)
- [8. Source Adapters](#8-source-adapters)
- [9. Document Ingestion](#9-document-ingestion)
- [10. Evidence Layer & Traceability](#10-evidence-layer--traceability)
- [11. Analytical Engines](#11-analytical-engines)
  - [Similarity Analysis](#similarity-analysis)
  - [Coverage Analysis](#coverage-analysis)
  - [Contradiction Detection](#contradiction-detection)
  - [Research Gap Analysis](#research-gap-analysis)
  - [Idea Collision Engine](#idea-collision-engine)
  - [Stress Testing](#stress-testing)
  - [Defensible Differentiation](#defensible-differentiation)
- [12. Research Graph & 3D Constellation](#12-research-graph--3d-constellation)
- [13. Traceable Report Generation](#13-traceable-report-generation)
- [14. Scientific Integrity & Language Guardrails](#14-scientific-integrity--language-guardrails)
- [15. Live Research vs. Simulated Demo Mode](#15-live-research-vs-simulated-demo-mode)
- [16. Repository Structure](#16-repository-structure)
- [17. Environment Variables](#17-environment-variables)
- [18. Local Setup & Execution Guide](#18-local-setup--execution-guide)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Database Setup & Migrations](#database-setup--migrations)
  - [Running the Redis Worker](#running-the-redis-worker)
- [19. Testing & Build Commands](#19-testing--build-commands)
- [20. API Endpoints & Swagger Documentation](#20-api-endpoints--swagger-documentation)
- [21. Example Walkthrough](#21-example-walkthrough)
- [22. Known Limitations & Production Roadmap](#22-known-limitations--production-roadmap)

---

## 1. Problem Being Solved

Technical innovators, researchers, and engineers waste hundreds of hours manually searching arXiv, Semantic Scholar, Crossref, and GitHub to discover whether their project idea has prior art, unaddressed vulnerabilities, or overlapping implementations. Existing tools either offer keyword search or produce LLM hallucinations claiming an idea is "100% unique" without verifiable evidence.

IdeaLens replaces hallucinated novelty claims with **verifiable, multi-source evidence linkage**, structured multidimensional similarity, and disciplined scientific disclosures.

---

## 2. What IdeaLens Does

1. **Ingests Ideas:** Accepts plain text input or uploaded documents (`.txt`, `.pdf`, `.docx`).
2. **Deconstructs Structure:** Decomposes ideas into problems, objectives, technologies, methods, datasets, architecture, claims, and research questions.
3. **Executes Staged Retrieval:** Queries arXiv, Crossref, GitHub, and Semantic Scholar with rate-limiting, retries, and backoff.
4. **Extracts Evidence:** Normalizes sources, eliminates duplicates, and extracts bounded excerpts linked to source identifiers (DOIs, arXiv IDs, URLs).
5. **Performs Multidimensional Analysis:** Evaluates similarity across separate dimensions (problem, method, dataset, technology, architecture) rather than calculating a single artificial "novelty score".
6. **Detects Contradictions & Gaps:** Identifies conflicting empirical findings and areas with sparse coverage.
7. **Stress-Tests Directions:** Evaluates research crowding, dataset availability, assumption dependencies, and evaluation bottlenecks.
8. **Visualizes the Research Graph:** Renders a 3D interactive constellation scene (Three.js / React Three Fiber) connecting the Idea Core to all evidence nodes.
9. **Generates Evidence-Grounded Reports:** Emits traceable markdown reports with explicit scope disclosures.

---

## 3. Core Research Workflow

```mermaid
flowchart TD
    A([User Submission: Idea Text / Document]) --> B[Document Validation & Ingestion]
    B --> C[Idea Decomposition: 8 Core Fields]
    C --> D[Multi-Angle Query Planning]
    D --> E[Outbound Parallel Retrieval: arXiv, Crossref, GitHub, Semantic Scholar]
    E --> F[Source Normalization & Canonical Deduplication]
    F --> G[Evidence Extraction & Provenance Linkage]
    G --> H[Multidimensional Similarity Engine]
    G --> I[Sufficiency Coverage Engine]
    G --> J[Contradiction Detection Engine]
    H & I --> K[Research Gap Analysis]
    C & G --> L[Idea Collision Engine]
    H & I --> M[Risk Stress-Testing Engine]
    H & K & L --> N[Defensible Differentiation Engine]
    F & G & I --> O[Research Graph Construction]
    H & I & J & K & L & M & N --> P[Traceable Report Assembly & Language Guardrail]
    P --> Q([Interactive 3D Constellation & Live Workspace])
```

---

## 4. High-Level Architecture

IdeaLens adopts a **modular monolith** architecture designed for resilience and auditability:

```
┌────────────────────────────────────────────────────────────┐
│                    Next.js Frontend                        │
│   (App Router, React Three Fiber, Tailwind, Lucide)        │
└──────────────┬───────────────────────────────▲─────────────┘
               │ HTTP POST / Upload            │ Polling & Artifact GET
               ▼                               │
┌──────────────────────────────────────────────┴─────────────┐
│                    FastAPI Backend                         │
│  - Document Ingestion (TXT, PDF, DOCX)                     │
│  - Staged Orchestration Pipeline (14 checkpointed stages)  │
│  - Analytics Engines (Similarity, Gaps, Collisions, etc.)  │
└──────────────┬───────────────────────────────▲─────────────┘
               │                               │
       ┌───────┴───────┐               ┌───────┴───────┐
       ▼               ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ PostgreSQL  │ │ Redis Queue │ │ In-Process  │ │ Outbound    │
│  (psycopg)  │ │ (Worker CLI)│ │ Executor    │ │ Adapters    │
│  or SQLite  │ │             │ │ (Fallback)  │ │ (HTTPX)     │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

- **Execution Safety:** The API returns `202 Accepted` immediately upon creation and delegates work asynchronously.
- **Resilient Fallback:** When Redis is absent, jobs run on the in-process background threadpool (`submit_local`). When PostgreSQL driver is absent, storage falls back to a local SQLite database (`idealens.db`).

---

## 5. Technology Stack

### Backend
- **Python 3.11+** (validated on Python 3.14)
- **FastAPI** & **Starlette**: Asynchronous REST API contracts
- **Pydantic v2**: Strict schema validation and serialization
- **SQLAlchemy 2.0**: Unified ORM for PostgreSQL and SQLite
- **Alembic**: Database migrations
- **HTTPX**: Outbound asynchronous HTTP client with exponential backoff and jitter
- **PyPDF** & **zipfile/XML**: Document ingestion engines
- **Pytest** & **Ruff**: Test suite and static analysis

### Frontend
- **Next.js 16 (Turbopack)**: React framework with App Router
- **TypeScript**: Strict compile-time typing
- **Tailwind CSS**: Dark-mode technical design system
- **React Three Fiber**, **Three.js**, **Drei**: 3D crystalline Idea Core and evidence constellation
- **Lucide React**: Clean technical iconography

---

## 6. Database & Persistence Layer

The database contains 19 mapped entities with foreign key constraints, indexes, and cascading rules:

| Table | Purpose |
|---|---|
| `research_runs` | Run lifecycle, status, timestamps, decomposition, snapshots, decision signals |
| `run_events` | Append-only event log with stage transitions and error tracking |
| `documents` | Ingested source files, metadata, MIME types, and SHA-256 hashes |
| `document_chunks` | Token-estimated slices with content hashes |
| `queries` | Generated multi-angle retrieval queries and execution statuses |
| `source_items` | Normalized records from adapters with canonical deduplication pointers |
| `evidence` | Specific excerpts with dimensions, confidence, and provenance backrefs |
| `claims` | Grounded statements extracted from evidence |
| `similarity_results` | Per-dimension similarity scores, confidences, and evidence links |
| `coverage_results` | Sufficiency evaluations per dimension (`strong`, `moderate`, `limited`, `insufficient`) |
| `contradictions` | Two-sided conflicting empirical findings across sources |
| `research_gaps` | Identified saturation classifications and standardized phrasing |
| `collision_combinations` | Multi-concept combinations and occurrence rates |
| `stress_tests` | Risks across saturation, assumptions, datasets, and bottlenecks |
| `differentiation_plans` | Concrete technical strategies to increase defensibility |
| `graph_nodes` | Visualization-agnostic entities (core, papers, repos, methods, etc.) |
| `graph_edges` | Semantic relationships (`cites`, `implements`, `evidence_for`, `conflicts_with`) |
| `reports` | Rendered markdown reports with citations and guardrail audit statuses |

---

## 7. Redis & Background Worker Model

- **Queue Structure:** FIFO queue using Redis list (`LPUSH` / `BLPOP`) via `QUEUE_KEY=idealens:research:queue`.
- **Worker Execution:**
  ```bash
  python -m app.workers.runner
  ```
- **Fallback Execution:** If Redis is down or unconfigured, `app.workers.dispatch` automatically routes tasks to `app.workers.local` (Python threadpool), preventing user disruption in local development environments.
- **Stage Checkpointing:** Each of the 14 stages writes its state to the database, allowing observability and post-crash audits.

---

## 8. Source Adapters

All adapters adhere to the strict `SourceAdapter` contract with rate limiting, timeouts, and structured error handling:

| Adapter | Provider | Protocol | Identifier Types |
|---|---|---|---|
| `semantic_scholar` | Semantic Scholar Graph API | REST (GET) | S2 Paper ID, DOI, arXiv ID, URL |
| `arxiv` | arXiv Export API | Atom XML | arXiv ID, PDF link |
| `crossref` | Crossref Works API | REST (GET) | DOI, Container Title, URL |
| `github` | GitHub Search API | REST (GET) | Repo Full Name, GitHub URL |

**Fault Tolerance:**
- HTTP 429 rate limits parse `Retry-After` headers and back off with jitter.
- Adapter failures are recorded as `source.failed` run events without aborting the entire research run.

---

## 9. Document Ingestion

Supported file formats:
- **Plain Text (`.txt`)**: Multi-encoding fallback (UTF-8, Latin-1, CP1252) with control character stripping.
- **PDF (`.pdf`)**: Safe parsing via `pypdf` with stream scanning; binary execution disabled. If a PDF contains only scanned raster images without selectable text, the API returns a structured `PDF_TEXT_NOT_FOUND` error rather than crashing.
- **Word (`.docx`)**: Safe `zipfile` extraction parsing `word/document.xml` using `xml.etree.ElementTree`.

**Security & Error Contract:**
- Size strictly capped at **10 MB** (returns `FILE_TOO_LARGE`).
- Empty files return `EMPTY_FILE`.
- Corrupted/unreadable headers return `MALFORMED_PDF`.
- Binary executable signatures (`MZ`, `ELF`, Mach-O) are rejected with `DANGEROUS_FILE_TYPE`.
- Extracted text is capped at 50,000 characters to prevent unbounded memory usage.
- Typing a new idea or selecting a new file immediately clears any stale upload errors.

---

## 9.1 Research History & Persistence

IdeaLens includes persistent research history backed directly by the SQL database:
- **Automatic History Tracking**: Every research run creates a persistent record with its full deconstructed idea title, creation timestamp, canonical source count, extracted evidence count, and completion status.
- **History Drawer**: Access prior research runs from the top navigation bar. Clicking any past idea instantly restores its complete analytical workspace, 3D constellation, evidence chain, and full-text report.
- **State Separation**: Input states, file upload errors, and research workspace states are strictly isolated, ensuring clean "+ New Idea" resets without cross-talk or stale error poisoning.

---

## 10. Evidence Layer & Traceability

Every analytical deduction is linked through a verifiable chain of custody:

$$\text{Conclusion} \longrightarrow \text{Claim} \longrightarrow \text{Evidence Record} \longrightarrow \text{Source Item} \longrightarrow \text{URL / DOI / arXiv ID}$$

- **Excerpts:** Bounded substrings preserved directly from retrieved text. No synthetic citations are permitted.
- **Provenance Backrefs:** Stored JSON mapping the exact originating document title, identifier, and URL.

---

## 11. Analytical Engines

### Similarity Analysis
Computes hybrid lexical (Jaccard on term vocabulary) and structured overlap (concept bigrams) per dimension: `problem`, `objective`, `technology`, `method`, `architecture`, `dataset`, and `evaluation`.
> **Policy:** Never produces a single "novelty score".

### Coverage Analysis
Evaluates evidence density per dimension into four standardized tiers:
- `strong`: $\ge 5$ items across $\ge 3$ distinct sources.
- `moderate`: $\ge 2$ items across $\ge 2$ distinct sources.
- `limited`: $\ge 1$ item retrieved.
- `insufficient`: 0 items retrieved in the searched corpus.

### Contradiction Detection
Identifies opposing lexical signals on shared technical subjects (e.g., one source reports significant performance degradation while another reports efficiency gains under different conditions). Both sides are preserved with comparability classifications.

### Research Gap Analysis
Identifies underexplored areas and concept combinations using standardized wording:
- `common`: Well-represented in the retrieved corpus.
- `moderately_represented`: Appears in multiple retrieved items.
- `limited_evidence_found`: Limited evidence retrieved.
- `insufficient_evidence`: Insufficient evidence retrieved.

### Idea Collision Engine
Analyzes pairwise and multi-concept combinations from the decomposed idea against the corpus to surface underexplored intersections.

### Stress Testing
Evaluates 4 critical project risk vectors:
1. **Research Saturation:** Overlap crowding in core dimensions.
2. **Dataset Availability:** Scarcity of standard evaluation benchmarks.
3. **Unsupported Assumptions:** Over-reliance on speculative assertion markers.
4. **Evidence Weaknesses:** Fragile single-source citations.

### Defensible Differentiation
Constructs evidence-referenced technical strategies to strengthen the idea's defensibility, specifying overlap boundaries, less-represented niches, and remaining uncertainties.

---

## 12. Research Graph & 3D Constellation

- **Data Model:** Nodes (`idea`, `problem`, `objective`, `technology`, `method`, `dataset`, `paper`, `repo`, `claim`, `evidence`) and typed edges (`uses`, `implements`, `supports`, `cites`, `similar_to`, `evidence_for`, `conflicts_with`).
- **3D Visualization:** React Three Fiber scene rendering:
  - **Idea Core:** Pulsing crystalline icosahedron with procedural wireframe glow.
  - **Constellation Nodes:** Color-coded 3D spheres positioned around the core.
  - **Connection Beams:** Dynamic glowing cylinders depicting semantic relationships.
  - **Interactivity:** Hover cards, click selection, and orbital controls.

---

## 13. Traceable Report Generation

Generates an audit-ready Markdown report structured into 12 sections:
1. Executive Summary & Idea Statement
2. Research Scope & Query Disclosure
3. Idea Decomposition
4. Evidence Sufficiency Coverage
5. Multidimensional Similarity
6. Empirical Contradictions
7. Research Gaps
8. Concept Collisions
9. Risk Stress-Testing
10. Defensible Differentiation Strategy
11. Corpus Limitations & Disclosures
12. Complete Citation Index

---

## 14. Scientific Integrity & Language Guardrails

To prevent misleading academic claims, the system enforces automated language guardrails. Every report is audited against a banned-phrase policy:

$$\text{Violations} = \left\{\text{"100\% novel"}, \text{"first-ever"}, \text{"no prior work"}, \text{"nobody has done this"}, \text{"guarantee of novelty"}, \dots\right\}$$

If any banned phrase is detected, the report status is flagged as `failed` and logged.

---

## 15. Live Research vs. Simulated Demo Mode

IdeaLens explicitly distinguishes between live and simulated runs:

| Attribute | LIVE RESEARCH ENGINE | DEMO / SIMULATED CORPUS |
|---|---|---|
| **Data Origin** | Real queries dispatched to arXiv, GitHub, Crossref, and Semantic Scholar | Local deterministic reference datasets in `frontend/lib/mock/` |
| **Database** | Fully persisted in PostgreSQL / SQLite | In-memory client-side preview |
| **UI Badge** | Green glowing badge: `LIVE RESEARCH ENGINE` | Amber badge: `DEMO / SIMULATED CORPUS` |
| **Trigger** | Submitting an idea via the active workspace input | Clicking the demo preview fallback button |

---

## 16. Repository Structure

```
ide-lens/
├── backend/
│   ├── alembic/                 # Database migrations
│   │   └── versions/            # Schema migration scripts
│   ├── app/
│   │   ├── analysis/            # Analytical engines (similarity, gaps, stress, etc.)
│   │   ├── api/routes/          # REST endpoints (health, research_runs, documents)
│   │   ├── core/                # Configuration, logging, settings
│   │   ├── db/                  # Engine setup, session factory, base models
│   │   ├── evidence/            # Evidence extraction from source items
│   │   ├── graph/               # Research graph construction
│   │   ├── models/              # SQLAlchemy ORM models (research & analysis)
│   │   ├── reports/             # Report assembly & language guardrail
│   │   ├── schemas/             # Pydantic validation models
│   │   ├── services/            # Ingestion, decomposition, query planning, retrieval
│   │   ├── sources/             # Adapters for arXiv, Crossref, GitHub, Semantic Scholar
│   │   └── workers/             # Redis queue, runner CLI, local threadpool fallback
│   ├── tests/                   # Pytest test suite
│   ├── alembic.ini              # Alembic configuration
│   └── pyproject.toml           # Python dependencies and tool configuration
├── frontend/
│   ├── app/                     # Next.js App Router (layout, global styling, page)
│   ├── components/              # LensScene (3D), ResearchDashboard (11 tabs)
│   ├── lib/
│   │   ├── api/                 # Typed API client and contract interfaces
│   │   └── mock/                # Demo corpus datasets and fallback repositories
│   ├── package.json             # Frontend dependencies
│   └── tsconfig.json            # TypeScript configuration
├── docs/                        # Architecture decisions, PRD, and data models
├── AUDIT_REPORT.md              # Historical milestone reports
└── README.md                    # Project documentation
```

---

## 17. Environment Variables

Create `backend/.env` by copying `backend/.env.example`:

```bash
# Runtime environment
ENVIRONMENT=development

# Security & Authentication Guardrails
# - "development_insecure_demo": unauthenticated local demo session
# - "enforced": strict Bearer JWT required for all user endpoints (HTTP 401 on missing/invalid token)
SECURITY_MODE=development_insecure_demo
JWT_SECRET_KEY=change-this-secret-key-in-production-deployments
JWT_ALGORITHM=HS256

# Database (PostgreSQL recommended; SQLite fallback used if absent)
# In production, set AUTO_INIT_SCHEMA=false and run `alembic upgrade head`
DATABASE_URL=postgresql+psycopg://idealens:idealens@localhost:5432/idealens
AUTO_INIT_SCHEMA=true

# Redis (queue infrastructure; local threadpool fallback used if absent)
REDIS_URL=redis://localhost:6379/0

# Reliable Worker Queue & Stale Run Recovery
QUEUE_KEY=idealens:research:queue
QUEUE_PROCESSING_KEY=idealens:research:processing
QUEUE_DLQ_KEY=idealens:research:dlq
QUEUE_BLOCK_SECONDS=5
WORKER_HEARTBEAT_TIMEOUT_SECONDS=180
WORKER_MAX_RETRIES=2

# Source Caching
SOURCE_CACHE_ENABLED=true
SOURCE_CACHE_TTL_SECONDS=86400

# Application Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_RESEARCH_RPM=10
RATE_LIMIT_DOCUMENTS_RPM=20

# Allowed CORS origins (JSON array)
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# Retrieval tuning
ENABLED_ADAPTERS=semantic_scholar,crossref,arxiv,github
RETRIEVAL_LIMIT_PER_SOURCE=10
RETRIEVAL_MAX_CONCURRENCY=4
HTTP_TIMEOUT_SECONDS=30.0
HTTP_MAX_RETRIES=3
EXCERPT_CHAR_LIMIT=500

# Optional API Keys (rate-limit enhancements)
# GITHUB_TOKEN=ghp_...
# SEMANTIC_SCHOLAR_API_KEY=...
# CROSSREF_MAILTO=researcher@example.com
```

Frontend configuration (optional; defaults to `http://127.0.0.1:8000`):
```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

---

## 18. Local Setup & Execution Guide

### Backend Setup

1. Navigate to `backend/` and create a virtual environment:
   ```bash
   cd backend
   python -m venv .venv
   ```
2. Activate virtual environment:
   - **Windows (PowerShell):** `.\.venv\Scripts\Activate.ps1`
   - **Linux/macOS:** `source .venv/bin/activate`
3. Install dependencies in editable mode:
   ```bash
   pip install -e ".[dev]"
   ```
4. Start the FastAPI backend server:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   Verify health:
   ```bash
   curl http://127.0.0.1:8000/health
   ```

### Frontend Setup

1. Navigate to `frontend/`:
   ```bash
   cd frontend
   npm install
   ```
2. Start the development server:
   ```bash
   npm run dev
   ```
3. Open `http://localhost:3000` in your browser.

### Database Setup & Production Migrations

In development mode, `AUTO_INIT_SCHEMA=true` automatically initializes SQLite tables.
For production deployments (PostgreSQL), set `AUTO_INIT_SCHEMA=false` and run:
```bash
cd backend
alembic upgrade head
```
Production startup explicitly checks schema readiness and refuses to create ad-hoc schema tables on the fly.
cd backend
alembic upgrade head
```
*(Note: When running without PostgreSQL, the application automatically boots with an embedded SQLite schema via FastAPI lifespan).*

### Running the Redis Worker

In a production or Redis-enabled setup, run the worker in a separate terminal:
```bash
cd backend
python -m app.workers.runner
```

---

## 19. Testing & Build Commands

### Backend Verification
Run the complete Pytest suite:
```bash
cd backend
python -m pytest tests/ -v
```
Run Ruff static analysis:
```bash
python -m ruff check app tests
```

### Frontend Verification
Run ESLint check:
```bash
cd frontend
npm run lint
```
Build production bundle:
```bash
npm run build
```

---

## 20. API Endpoints & Swagger Documentation

Interactive Swagger documentation is available at:
`http://127.0.0.1:8000/docs`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service status, environment, and dependency probe |
| `POST` | `/api/v1/documents/upload` | Upload and chunk `.txt`, `.pdf`, or `.docx` file |
| `GET` | `/api/v1/documents/{id}` | Retrieve document metadata and extracted text |
| `POST` | `/api/v1/research-runs` | Create and enqueue asynchronous research run |
| `GET` | `/api/v1/research-runs` | List research runs with pagination |
| `GET` | `/api/v1/research-runs/{id}` | Get run progress, current stage, and status |
| `GET` | `/api/v1/research-runs/{id}/evidence` | List all extracted evidence records |
| `GET` | `/api/v1/research-runs/{id}/similarity` | Multidimensional similarity breakdown |
| `GET` | `/api/v1/research-runs/{id}/coverage` | Dimension evidence sufficiency levels |
| `GET` | `/api/v1/research-runs/{id}/contradictions` | Conflicting empirical evidence pairs |
| `GET` | `/api/v1/research-runs/{id}/gaps` | Identified research gaps and saturation signals |
| `GET` | `/api/v1/research-runs/{id}/collisions` | Component collision and co-occurrence counts |
| `GET` | `/api/v1/research-runs/{id}/stress-test` | Stress testing and vulnerability assessment |
| `GET` | `/api/v1/research-runs/{id}/differentiation` | Defensible differentiation recommendations |
| `GET` | `/api/v1/research-runs/{id}/graph` | Nodes and edges for research graph visualization |
| `GET` | `/api/v1/research-runs/{id}/report` | Complete traceable Markdown report and citations |

---

## 21. Example Walkthrough

1. Start both backend (`:8000`) and frontend (`:3000`).
2. Navigate to `http://localhost:3000`.
3. In the input box, enter:
   > *"Deterministic graph reasoning with temporal knowledge bases and contrastive verification for autonomous multimodal agents"*
4. (Optional) Upload an accompanying architectural specification (`.pdf` or `.docx`).
5. Click **Run Live Research**.
6. Observe the progress bar advance through `decomposition` $\rightarrow$ `retrieval` $\rightarrow$ `evidence` $\rightarrow$ `analysis` $\rightarrow$ `report`.
7. Explore the **3D Constellation Scene** to inspect linked evidence nodes.
8. Switch across the 11 analytical workspace tabs (**Similarity**, **Coverage**, **Contradictions**, **Gaps**, **Stress Test**, etc.) to view evidence-backed signals.

---

## 22. Known Limitations & Production Roadmap

- **Public Rate Limits:** When running without API keys, Semantic Scholar public endpoints frequently return HTTP 429. Exponential backoff handles this, but providing `SEMANTIC_SCHOLAR_API_KEY` is strongly recommended for high throughput.
- **Scanned Image PDFs:** PDFs consisting entirely of scanned raster images require OCR preprocessing before upload; only selectable text streams are extracted.
- **Full-Text Papers:** Retrievals rely primarily on titles, abstracts, descriptions, and metadata. Ingesting full 30-page academic PDFs is bounded by the 50,000 character buffer to respect publisher policies and memory constraints.
- **Authentication:** Current endpoints are open. Multi-tenant user authentication and organization boundaries are targeted for the next release.

---

## License

IdeaLens is released under the [MIT License](LICENSE).