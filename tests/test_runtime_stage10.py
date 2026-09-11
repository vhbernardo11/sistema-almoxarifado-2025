from __future__ import annotations

from types import SimpleNamespace

from integra.approval import InMemoryApprovalStore
from integra.approval.gate import canonical_digest
from integra.autonomy import InMemoryQueueStore
from integra.memory.store import InMemoryMemoryStore
from integra.runtime import build_stage10_handlers, build_stage10_worker
from integra.text_core.models import CopyPackage, ResearchBrief, ResearchSource, StrategyBrief


def _research() -> ResearchBrief:
    return ResearchBrief(
        objective="Apresentar o IntegraTrampo a eletricistas de teste",
        audience_insights=["Profissionais valorizam oportunidades claras e locais"],
        market_context=["Teste de homologação sem promessa de contratação"],
        opportunities=["Explicar a proposta de conexão"],
        risks=["Não prometer renda ou contratação"],
        facts_to_use=["A campanha apresenta uma plataforma de conexão"],
        sources=[ResearchSource(title="Fonte sintética de teste", url="https://example.org/stage10", note="Fixture determinística; não representa pesquisa ao vivo.")],
        confidence="medium",
    )


def _strategy() -> StrategyBrief:
    return StrategyBrief(
        objective="Gerar interesse qualificado em ambiente de teste",
        positioning="Ponte entre demanda e profissionais",
        core_message="Novas conexões podem começar pelo IntegraTrampo",
        promise="Facilitar a descoberta de oportunidades e profissionais",
        proof_points=["Fluxo simples de conexão"], objections=["Não existe promessa de contratação"],
        content_angle="Ser encontrado por quem precisa do serviço", call_to_action="Conheça o IntegraTrampo",
        guardrails=["Não prometer renda", "Não inventar números"],
    )


def _copy() -> CopyPackage:
    return CopyPackage(
        headline="Seu próximo contato pode começar aqui",
        primary_copy="O IntegraTrampo aproxima quem precisa de um serviço de quem sabe fazer.",
        short_caption="Mostre seu trabalho. Crie novas conexões.",
        long_caption="Teste controlado de uma campanha textual para aproximar demanda e profissionais.",
        call_to_action="Conheça o IntegraTrampo", hashtags=["#IntegraTrampo"],
        visual_brief="Eletricista em contexto real de trabalho; CTA visível.",
        claims_used=["A campanha apresenta uma plataforma de conexão"],
    )


def _fake_runner():
    outputs = [_research(), _strategy(), _copy()]
    calls = {"n": 0}
    def run(_agent, _prompt):
        value = outputs[calls["n"]]
        calls["n"] += 1
        return SimpleNamespace(final_output=value)
    return run


def test_stage10_real_text_pipeline_creates_pending_approval_for_test_actor():
    queue = InMemoryQueueStore(); memory = InMemoryMemoryStore(); approvals = InMemoryApprovalStore()
    worker = build_stage10_worker(worker_id="stage10-test-worker", queue_store=queue, memory_store=memory, approval_store=approvals, text_runner=_fake_runner())
    job = queue.enqueue(job_type="text_core.run", payload={
        "test_mode": True, "test_actor_id": "stage8-test-user-001",
        "request": {"goal": "Criar campanha de teste do IntegraTrampo para eletricistas", "audience": "Eletricistas autônomos", "location": "Teodoro Sampaio, SP"},
    })
    tick = worker.tick(); stored = queue.jobs[job.id].result; approval = approvals.get(stored["approval_id"])
    assert tick.job_status == "completed"
    assert stored["waiting_approval"] is True
    assert stored["publication_authorized"] is False
    assert stored["result"]["publication_authorized"] is False
    assert approval.decision == "pending"
    assert approval.content_digest == canonical_digest(stored["result"])
    assert approval.metadata["test_mode"] is True
    assert approval.metadata["test_actor_id"] == "stage8-test-user-001"
    assert approval.metadata["preview"]["headline"] == "Seu próximo contato pode começar aqui"


def test_stage10_publisher_is_absent_and_real_actor_fails_closed():
    memory = InMemoryMemoryStore(); approvals = InMemoryApprovalStore()
    handlers = build_stage10_handlers(memory_store=memory, approval_store=approvals, text_runner=_fake_runner())
    assert "publisher.execute" not in handlers
    queue = InMemoryQueueStore()
    worker = build_stage10_worker(worker_id="stage10-test-worker", queue_store=queue, memory_store=memory, approval_store=approvals, text_runner=_fake_runner())
    job = queue.enqueue(job_type="text_core.run", payload={"test_mode": True, "test_actor_id": "real-user-001", "request": {"goal": "Criar campanha textual de teste controlado"}}, max_attempts=1)
    tick = worker.tick()
    assert tick.job_status == "failed"
    assert "usuários de teste" in (queue.jobs[job.id].last_error or "")
