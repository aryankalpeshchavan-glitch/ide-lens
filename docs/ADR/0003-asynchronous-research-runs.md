# ADR-0003: Asynchronous Research Runs

**Status:** Accepted (M0 decision). **Date:** 2026-09-01 (M0).

## Context

A research run — retrieval across four or more external APIs, evidence extraction, similarity/gap/contradiction analysis, and report generation — takes from seconds to minutes or more. The API client should not hold an HTTP connection open for that duration; runs must survive worker crashes; partial failures must be disclosed per source and stage; and reproducibility requires full run-history persistence.

Options: synchronous long-lived request (block until completion); async job queue (Redis) with status polling; webhooks; server-sent events/WebSockets.

## Decision

Research is **asynchronous**:

- `POST /research-runs` validates and persists a `ResearchRun` (status `queued`), enqueues background work (Redis queue), and responds immediately with `202` and a `run_id`/`status_url`. The client polls; no long-lived HTTP connection is held (PRD non-goal).
- A worker process (ADR-0001) consumes jobs and executes the staged pipeline (ARCHITECTURE.md §3). Every stage persists its artifacts plus `state_history` before proceeding (stage checkpointing), so a crashed worker resumes from the last persisted stage rather than restarting blindly (FAILURE_HANDLING.md §8).
- Every run has a persistent identity (UUID), a status (`queued → running → completed | partially_failed | failed`), and full state history (JSONB). Runs are never ephemeral: inputs, generated queries, sources, retrieval timestamps, evidence, analysis, scoring configuration, provider/model information, report information, errors, and partial failures are persisted (DATA_MODEL.md).
- Queue visibility timeout is set greater than the longest stage, so a crashed worker causes a requeue; idempotent stages and at-most-once enqueue make re-execution safe.
- Status polling is the MVP contract; webhooks, SSE, or WebSockets are **Proposed** for later iterations.

## Alternatives considered

- **Synchronous request-response:** simplest client contract, but unacceptable for minute-scale runs (timeouts, worker/connection coupling, poor UX). **Rejected.**
- **Fire-and-forget with no status:** too simple to be usable — no progress, no partial-failure visibility, no reproducibility story. **Rejected.**
- **Webhooks at MVP:** push results, but require callback endpoints, delivery retry semantics, and more moving parts; polling suffices for MVP report UX. **Deferred** (Proposed for M1+).
- **In-process async only:** no durable queue, poor worker-crash/requeue behavior, weak run recovery. **Rejected** (Redis queue decided).

## Consequences

- **Positive:** bounded client connections; run durability and recovery via checkpointing; partial-failure disclosure per stage/source; reproducibility anchored to persisted run artifacts; simple MVP polling contract; scales by adding workers.
- **Negative/costs:** extra infrastructure (Redis queue); idempotency and at-most-once semantics required; a sweeper/heartbeat for stale `running` runs (Proposed); polling UX in the UI (MVP); push models remain **Open**.

## Related

ADR-0001, ADR-0002, ARCHITECTURE.md §3–§4, FAILURE_HANDLING.md §2 and §8, DATA_MODEL.md (ResearchRun, RunEvent).