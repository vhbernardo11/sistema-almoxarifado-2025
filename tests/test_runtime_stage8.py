from __future__ import annotations

import pytest

from integra.autonomy import InMemoryQueueStore
from integra.memory.store import InMemoryMemoryStore
from integra.runtime import (
    TestModeViolation,
    build_stage8_handlers,
    build_stage8_worker,
    require_stage8_test_actor,
)


def test_stage8_rejects_non_test_actor():
    with pytest.raises(TestModeViolation):
        require_stage8_test_actor({"test_mode": False, "test_actor_id": "real-user"})
    with pytest.raises(TestModeViolation):
        require_stage8_test_actor({"test_mode": True, "test_actor_id": "user-123"})


def test_stage8_handler_registry_connects_real_pipelines_but_not_publisher():
    memory = InMemoryMemoryStore()
    handlers = build_stage8_handlers(memory_store=memory)
    assert "text_core.run" in handlers
    assert "media.review" in handlers
    assert "test.echo" in handlers
    assert "publisher.execute" not in handlers


def test_stage8_test_echo_runs_through_worker():
    queue = InMemoryQueueStore()
    memory = InMemoryMemoryStore()
    worker = build_stage8_worker(
        worker_id="stage8-test-worker",
        queue_store=queue,
        memory_store=memory,
    )
    job = queue.enqueue(
        job_type="test.echo",
        payload={
            "test_mode": True,
            "test_actor_id": "stage8-test-user-001",
            "message": "ping",
        },
    )
    result = worker.tick()
    assert result.job_status == "completed"
    assert queue.jobs[job.id].result["echoed"] == "ping"
    assert queue.jobs[job.id].result["test_actor_id"] == "stage8-test-user-001"


def test_stage8_waiting_approval_never_authorizes_publication():
    queue = InMemoryQueueStore()
    memory = InMemoryMemoryStore()
    worker = build_stage8_worker(
        worker_id="stage8-test-worker",
        queue_store=queue,
        memory_store=memory,
    )
    job = queue.enqueue(
        job_type="test.waiting_approval",
        payload={"test_mode": True, "test_actor_id": "stage8-test-admin-001"},
    )
    assert worker.tick().job_status == "completed"
    stored = queue.jobs[job.id].result
    assert stored["waiting_approval"] is True
    assert stored["publication_authorized"] is False


def test_stage8_publisher_job_fails_closed_even_for_test_actor():
    queue = InMemoryQueueStore()
    memory = InMemoryMemoryStore()
    worker = build_stage8_worker(
        worker_id="stage8-test-worker",
        queue_store=queue,
        memory_store=memory,
    )
    queue.enqueue(
        job_type="publisher.execute",
        payload={"test_mode": True, "test_actor_id": "stage8-test-admin-001"},
    )
    result = worker.tick()
    assert result.job_status == "failed"
    assert "handler ausente" in (result.detail or "")
