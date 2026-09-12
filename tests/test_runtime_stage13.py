from integra.autonomy import InMemoryQueueStore, Worker
from integra.runtime.handlers import build_stage8_handlers
from integra.runtime.stage13 import SPECIALIST_JOB_TYPES, enqueue_specialist_task
from integra.specialists import SpecialistTask


class DummyMemoryStore:
    pass


def worker(store):
    return Worker(
        worker_id="stage13-test-worker",
        store=store,
        handlers=build_stage8_handlers(memory_store=DummyMemoryStore()),
    )


def test_all_stage13_job_types_are_registered():
    handlers = build_stage8_handlers(memory_store=DummyMemoryStore())
    assert set(SPECIALIST_JOB_TYPES.values()).issubset(handlers)
    assert "publisher.execute" not in handlers


def test_programmer_and_tester_flow_through_queue():
    store = InMemoryQueueStore()
    program = SpecialistTask(
        specialist_id="programmer",
        actor_id="stage8-test-user-001",
        objective="Criar configuração sintética",
        payload={"workspace": {}, "operations": [{"action": "write_file", "path": "config.json", "content": '{"ok": true}'}]},
    )
    enqueue_specialist_task(store, program, idempotency_key="stage13-programmer-1")
    tick = worker(store).tick()
    assert tick.job_status == "completed"
    completed = next(iter(store.jobs.values()))
    assert completed.result["specialist_id"] == "programmer"
    workspace = completed.result["specialist_result"]["data"]["workspace"]

    testing = SpecialistTask(
        specialist_id="tester",
        actor_id="stage8-test-user-001",
        objective="Validar configuração sintética",
        payload={"workspace": workspace, "checks": [{"kind": "json_valid", "path": "config.json"}]},
    )
    enqueue_specialist_task(store, testing, idempotency_key="stage13-tester-1")
    worker(store).run_until_idle(max_jobs=5)
    tester_jobs = [j for j in store.jobs.values() if j.job_type == "specialist.tester"]
    assert tester_jobs[0].status == "completed"
    assert tester_jobs[0].result["specialist_result"]["data"]["passed"] is True


def test_specialist_job_never_authorizes_external_effects():
    store = InMemoryQueueStore()
    task = SpecialistTask(
        specialist_id="commercial",
        actor_id="stage8-test-user-001",
        objective="Montar roteiro comercial sintético",
        payload={"offer_name": "IntegraTrampo", "audience": "profissionais locais", "cta": "Cadastre-se", "benefits": ["receber oportunidades"]},
    )
    enqueue_specialist_task(store, task)
    worker(store).tick()
    job = next(iter(store.jobs.values()))
    assert job.status == "completed"
    assert job.result["publication_authorized"] is False
    assert job.result["external_actions_authorized"] is False


def test_real_actor_is_blocked_before_enqueue():
    store = InMemoryQueueStore()
    task = SpecialistTask(
        specialist_id="analytics",
        actor_id="usuario-real-001",
        objective="Analisar métricas",
        payload={"current": {"visits": 10}},
    )
    try:
        enqueue_specialist_task(store, task)
    except Exception as exc:
        assert "stage8-test" in str(exc)
    else:
        raise AssertionError("ator real deveria ser bloqueado")


def test_legal_review_is_visible_as_waiting_human_review():
    store = InMemoryQueueStore()
    task = SpecialistTask(
        specialist_id="legal_reviewer",
        actor_id="stage8-test-admin-001",
        objective="Triar contrato sintético",
        payload={"text": "Contrato com renovação automática, multa e tratamento de dados pessoais.", "jurisdiction": "BR"},
    )
    enqueue_specialist_task(store, task)
    worker(store).tick()
    job = next(iter(store.jobs.values()))
    assert job.result["requires_human_review"] is True
    assert job.result["waiting_approval"] is True
    assert job.result["publication_authorized"] is False
