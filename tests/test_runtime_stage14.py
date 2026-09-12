import pytest

from integra.autonomy import InMemoryQueueStore, Worker
from integra.maestro import WorkRequest
from integra.runtime.handlers import build_stage8_handlers
from integra.runtime.stage14 import (
    Stage14WorkflowRequest,
    enqueue_stage14_workflow,
    run_stage14_workflow,
)


class DummyMemoryStore:
    pass


def _worker(store):
    return Worker(
        worker_id="stage14-test-worker",
        store=store,
        handlers=build_stage8_handlers(memory_store=DummyMemoryStore()),
    )


def test_campaign_route_runs_second_wave_and_stops_for_human_review():
    request = Stage14WorkflowRequest(
        actor_id="stage8-test-user-001",
        work=WorkRequest(objective="Criar campanha sintética para o IntegraTrampo", kind="campaign"),
        step_payloads={
            "researcher": {
                "facts": ["IntegraTrampo conecta profissionais a oportunidades."],
                "sources": [{"label": "brief interno", "url": ""}],
            },
            "strategist": {
                "goal": "explicar o valor do cadastro",
                "audience": "profissionais locais",
                "facts": {"$step": "researcher", "path": "data.facts"},
            },
            "copywriter": {
                "headline": "Oportunidades mais perto de você",
                "body_points": ["Cadastre seu perfil", "Mostre seu trabalho"],
                "cta": "Cadastre-se",
                "facts": {"$step": "researcher", "path": "data.facts"},
            },
            "reviewer": {
                "artifact": {"$step": "copywriter", "path": "data"},
                "required_fields": ["headline", "short_caption", "call_to_action"],
            },
        },
    )
    result = run_stage14_workflow(request)
    assert result.route == "campaign"
    assert [step.specialist_id for step in result.steps] == ["researcher", "strategist", "copywriter", "reviewer"]
    assert result.status == "needs_review"
    assert result.requires_human_review is True
    assert result.publication_authorized is False
    assert result.external_actions_authorized is False
    assert result.steps[-1].result["data"]["ready_for_human_review"] is True


def test_software_route_passes_programmer_workspace_to_tester():
    request = Stage14WorkflowRequest(
        actor_id="stage8-test-user-001",
        work=WorkRequest(objective="Criar sistema sintético de configuração", kind="software"),
        step_payloads={
            "researcher": {"facts": ["O arquivo de configuração deve ser JSON válido."]},
            "programmer": {
                "workspace": {},
                "operations": [{"action": "write_file", "path": "config.json", "content": '{"ok": true}'}],
            },
            "tester": {
                "workspace": {"$step": "programmer", "path": "data.workspace"},
                "checks": [{"kind": "json_valid", "path": "config.json"}],
            },
            "reviewer": {
                "artifact": {"$step": "tester", "path": "data"},
                "required_fields": ["passed", "checks"],
            },
        },
    )
    result = run_stage14_workflow(request)
    tester = next(step for step in result.steps if step.specialist_id == "tester")
    assert tester.result["data"]["passed"] is True
    assert result.status == "needs_review"


def test_stage14_queue_handler_is_registered_and_fail_closed():
    store = InMemoryQueueStore()
    request = Stage14WorkflowRequest(
        actor_id="stage8-test-admin-001",
        work=WorkRequest(objective="Fazer triagem jurídica sintética", kind="legal"),
        step_payloads={
            "researcher": {"facts": ["Contrato contém renovação automática."]},
            "legal_reviewer": {"text": "Contrato com renovação automática e multa.", "jurisdiction": "BR"},
            "reviewer": {
                "artifact": {"$step": "legal_reviewer", "path": "data"},
                "required_fields": ["risk_flags", "flag_count"],
            },
        },
    )
    enqueue_stage14_workflow(store, request, idempotency_key="stage14-legal-1")
    tick = _worker(store).tick()
    assert tick.job_status == "completed"
    job = next(iter(store.jobs.values()))
    assert job.result["waiting_approval"] is True
    assert job.result["publication_authorized"] is False
    assert job.result["external_actions_authorized"] is False


def test_real_actor_is_blocked():
    request = Stage14WorkflowRequest(
        actor_id="usuario-real-001",
        work=WorkRequest(objective="Criar campanha de teste", kind="campaign"),
        step_payloads={},
    )
    with pytest.raises(Exception, match="stage8-test"):
        run_stage14_workflow(request)


def test_missing_step_payload_blocks_without_external_effect():
    request = Stage14WorkflowRequest(
        actor_id="stage8-test-user-001",
        work=WorkRequest(objective="Analisar métricas sintéticas", kind="analytics"),
        step_payloads={"analytics": {"current": {"visits": 100}}},
    )
    result = run_stage14_workflow(request)
    assert result.status == "blocked"
    assert result.blockers
    assert result.publication_authorized is False
    assert result.external_actions_authorized is False
