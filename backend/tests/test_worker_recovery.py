"""Tests for reliable worker queue patterns, heartbeat tracking, and stale run recovery."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.db.session import SessionLocal
from app.models.research import ResearchRunORM
from app.services.runs import STATUS_FAILED, STATUS_QUEUED, STATUS_RUNNING, recover_stale_runs
from app.workers.queue import ack_run, dequeue_run_reliable, enqueue_run


def test_reliable_queue_ack_flow(monkeypatch):
    """Test the queue -> processing -> ack lifecycle using mocked Redis client."""
    queue_storage = []
    processing_storage = []

    class MockRedisClient:
        def rpush(self, key, val):
            if "processing" in key or "dlq" in key:
                processing_storage.append(val)
            else:
                queue_storage.append(val)

        def brpoplpush(self, src, dst, timeout=5):
            if queue_storage:
                item = queue_storage.pop(0)
                processing_storage.append(item)
                return item.encode("utf-8")
            return None

        def lrem(self, key, count, val):
            if val in processing_storage:
                processing_storage.remove(val)
                return 1
            return 0

        def close(self):
            pass

    monkeypatch.setattr("app.workers.queue.build_redis_client", lambda: MockRedisClient())

    test_run_id = uuid4()
    # 1. Enqueue
    assert enqueue_run(test_run_id) is True
    assert str(test_run_id) in queue_storage

    # 2. Reliable dequeue moves to processing
    claimed = dequeue_run_reliable(timeout=1)
    assert claimed == str(test_run_id)
    assert str(test_run_id) not in queue_storage
    assert str(test_run_id) in processing_storage

    # 3. Acknowledge removes from processing
    assert ack_run(test_run_id) is True
    assert str(test_run_id) not in processing_storage


def test_stale_run_recovery_with_heartbeat_timeout(monkeypatch):
    """A running run with stale heartbeat is recovered and re-enqueued until retry limit."""
    session = SessionLocal()

    stale_time = datetime.now(UTC) - timedelta(seconds=300)
    run_id = uuid4()
    run = ResearchRunORM(
        id=run_id,
        idea="Stale run test idea",
        status=STATUS_RUNNING,
        progress=45,
        current_stage="retrieval",
        last_heartbeat_at=stale_time,
        retry_count=0,
    )
    session.add(run)
    session.commit()

    re_enqueued = []
    monkeypatch.setattr(
        "app.workers.queue.re_enqueue_stale_job",
        lambda rid: re_enqueued.append(rid),
    )

    # Trigger recovery with 180s threshold
    recovered = recover_stale_runs(session, timeout_seconds=180, max_retries=3)
    assert run_id in recovered

    session.refresh(run)
    assert run.status == STATUS_QUEUED
    assert run.retry_count == 1
    assert run_id in re_enqueued

    # Advance retry_count to max and trigger again
    run.retry_count = 3
    run.status = STATUS_RUNNING
    run.last_heartbeat_at = stale_time
    session.commit()

    dlq_jobs = []
    monkeypatch.setattr(
        "app.workers.queue.move_to_dlq",
        lambda rid, reason="": dlq_jobs.append(rid),
    )

    recovered_second = recover_stale_runs(session, timeout_seconds=180, max_retries=3)
    assert run_id in recovered_second

    session.refresh(run)
    assert run.status == STATUS_FAILED
    assert any(err.get("class") == "WORKER_TIMEOUT" for err in (run.error_summary or []))
    assert run_id in dlq_jobs
    session.close()
