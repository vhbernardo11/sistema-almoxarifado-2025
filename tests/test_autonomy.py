from __future__ import annotations

from datetime import datetime, timedelta, timezone

from integra.autonomy import InMemoryQueueStore, RetryPolicy, Worker


class Clock:
    def __init__(self):
        self.now = datetime(2026, 9, 11, 8, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.now

    def advance(self, seconds: int):
        self.now += timedelta(seconds=seconds)


def test_priority_and_idempotency():
    clock = Clock()
    store = InMemoryQueueStore(now_fn=clock)
    low = store.enqueue(job_type="x", payload={}, priority=10, idempotency_key="a")
    same = store.enqueue(job_type="x", payload={"ignored": True}, priority=999, idempotency_key="a")
    high = store.enqueue(job_type="x", payload={}, priority=20)
    assert same.id == low.id
    assert store.claim_next(worker_id="w").id == high.id


def test_retry_then_success():
    clock = Clock()
    store = InMemoryQueueStore(now_fn=clock)
    calls = {"n": 0}

    def flaky(job):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("temporário")
        return {"ok": True}

    store.enqueue(job_type="flaky", payload={}, max_attempts=3)
    worker = Worker(
        worker_id="w",
        store=store,
        handlers={"flaky": flaky},
        retry_policy=RetryPolicy(base_seconds=10),
    )
    first = worker.tick()
    assert first.job_status == "retry"
    assert worker.tick().claimed_job_id is None
    clock.advance(10)
    second = worker.tick()
    assert second.job_status == "completed"


def test_max_attempts_becomes_failed():
    clock = Clock()
    store = InMemoryQueueStore(now_fn=clock)
    store.enqueue(job_type="bad", payload={}, max_attempts=2)
    worker = Worker(
        worker_id="w",
        store=store,
        handlers={"bad": lambda job: (_ for _ in ()).throw(RuntimeError("boom"))},
        retry_policy=RetryPolicy(base_seconds=5),
    )
    assert worker.tick().job_status == "retry"
    clock.advance(5)
    assert worker.tick().job_status == "failed"


def test_stale_running_job_is_recovered():
    clock = Clock()
    store = InMemoryQueueStore(now_fn=clock)
    job = store.enqueue(job_type="x", payload={}, max_attempts=3)
    store.claim_next(worker_id="dead-worker")
    clock.advance(301)
    assert store.requeue_stale(stale_after_seconds=300) == 1
    assert store.jobs[job.id].status == "retry"
    assert store.claim_next(worker_id="new-worker").id == job.id


def test_schedule_materializes_one_slot():
    clock = Clock()
    store = InMemoryQueueStore(now_fn=clock)
    store.create_schedule(
        name="hourly",
        job_type="digest",
        payload={"kind": "daily"},
        interval_seconds=3600,
        next_run_at=clock(),
    )
    assert store.materialize_due_schedules() == 1
    assert store.materialize_due_schedules() == 0
    assert len(store.jobs) == 1


def test_worker_missing_handler_fails_closed():
    clock = Clock()
    store = InMemoryQueueStore(now_fn=clock)
    store.enqueue(job_type="unknown", payload={}, max_attempts=5)
    result = Worker(worker_id="w", store=store, handlers={}).tick()
    assert result.job_status == "failed"
    assert "handler ausente" in (result.detail or "")


def test_run_until_idle_has_explicit_limit():
    clock = Clock()
    store = InMemoryQueueStore(now_fn=clock)
    for _ in range(5):
        store.enqueue(job_type="x", payload={})
    worker = Worker(worker_id="w", store=store, handlers={"x": lambda job: {"ok": True}})
    results = worker.run_until_idle(max_jobs=3)
    assert len(results) == 3
    assert sum(1 for j in store.jobs.values() if j.status == "completed") == 3
