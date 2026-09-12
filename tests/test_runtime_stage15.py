import pytest

from integra.autonomy import InMemoryQueueStore, Worker
from integra.maestro import WorkRequest
from integra.runtime.handlers import build_stage8_handlers
from integra.runtime.stage15 import (
    Stage15WorkflowRequest,
    advance_stage15_workflow,
    enqueue_stage15_workflow,
)
from integra.specialists import execute_specialist


class DummyMemoryStore:
    pass


def _request():
    return Stage15WorkflowRequest(
        actor_id="stage8-test-user-001",
        work=WorkRequest(objective="Criar sistema sintético durável", kind="software"),
        step_payloads={
            "researcher": {"facts": ["Configuração deve ser JSON válido."]},
            "programmer": {"workspace": {}, "operations": [{"action": "write_file", "path": "config.json", "content": '{"ok": true}'}]},
            "tester": {"workspace": {"$step": "programmer", "path": "data.workspace"}, "checks": [{"kind": "json_valid", "path": "config.json"}]},
            "reviewer": {"artifact": {"$step": "tester", "path": "data"}, "required_fields": ["passed", "checks"]},
        },
    )


def test_resume_skips_already_completed_steps():
    calls = []
    def counting_executor(task):
        calls.append(task.specialist_id)
        return execute_specialist(task)

    request = _request()
    partial = advance_stage15_workflow(request, max_steps=2, executor=counting_executor)
    assert partial.status == "interrupted"
    assert partial.next_sequence == 2
    assert calls == ["researcher", "programmer"]

    final = advance_stage15_workflow(request, state=partial, executor=counting_executor)
    assert final.status == "needs_review"
    assert final.next_sequence == 4
    assert calls == ["researcher", "programmer", "tester", "reviewer"]
    assert final.completed["tester"]["data"]["passed"] is True
    assert final.publication_authorized is False
    assert final.external_actions_authorized is False


def test_checkpoint_cannot_cross_actor_boundary():
    request = _request()
    partial = advance_stage15_workflow(request, max_steps=1)
    other = request.model_copy(update={"actor_id": "stage8-test-admin-001"})
    with pytest.raises(Exception, match="Checkpoint"):
        advance_stage15_workflow(other, state=partial)


def test_missing_payload_blocks_and_preserves_fail_closed():
    request = Stage15WorkflowRequest(
        actor_id="stage8-test-user-001",
        work=WorkRequest(objective="Analisar métricas sintéticas", kind="analytics"),
        step_payloads={"analytics": {"current": {"visits": 100}}},
    )
    state = advance_stage15_workflow(request)
    assert state.status == "blocked"
    assert state.next_sequence == 1
    assert state.blockers
    assert state.publication_authorized is False
    assert state.external_actions_authorized is False


def test_real_actor_is_blocked():
    request = _request().model_copy(update={"actor_id": "usuario-real-001"})
    with pytest.raises(Exception, match="stage8-test"):
        advance_stage15_workflow(request)


def test_stage15_queue_type_registered_without_publisher():
    store = InMemoryQueueStore()
    enqueue_stage15_workflow(store, _request(), idempotency_key="stage15-durable-1")
    handlers = build_stage8_handlers(memory_store=DummyMemoryStore())
    assert "maestro.workflow.v2" in handlers
    assert "publisher.execute" not in handlers
    worker = Worker(worker_id="stage15-test", store=store, handlers=handlers)
    tick = worker.tick()
    assert tick.job_status == "completed"
    job = next(iter(store.jobs.values()))
    assert job.result["runtime"] == "stage15-python"
    assert job.result["waiting_approval"] is True
    assert job.result["publication_authorized"] is False
