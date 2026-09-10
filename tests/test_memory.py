from __future__ import annotations

from types import SimpleNamespace

import pytest

from integra.memory import InMemoryMemoryStore
from integra.text_core.models import (
    CampaignRequest,
    CopyPackage,
    ResearchBrief,
    ResearchSource,
    StrategyBrief,
)
from integra.text_core.persistent import run_text_core_persistent


def _outputs():
    return [
        ResearchBrief(
            objective="Pesquisar",
            audience_insights=["insight"],
            market_context=["contexto"],
            opportunities=["oportunidade"],
            risks=["risco"],
            facts_to_use=["fato"],
            sources=[ResearchSource(title="Fonte", url="https://example.org", note="teste")],
            confidence="medium",
        ),
        StrategyBrief(
            objective="Estratégia",
            positioning="posição",
            core_message="mensagem",
            promise="promessa moderada",
            proof_points=["prova"],
            objections=["objeção"],
            content_angle="ângulo",
            call_to_action="Conheça",
            guardrails=["não prometer resultado"],
        ),
        CopyPackage(
            headline="Headline",
            primary_copy="Texto principal",
            short_caption="Legenda curta",
            long_caption="Legenda longa",
            call_to_action="Conheça",
            visual_brief="Brief visual",
        ),
    ]


def test_persistent_pipeline_records_tasks_checkpoints_and_never_authorizes_publication():
    store = InMemoryMemoryStore()
    outputs = _outputs()
    cursor = {"value": 0}

    def runner(agent, prompt):
        output = outputs[cursor["value"]]
        cursor["value"] += 1
        return SimpleNamespace(final_output=output)

    result = run_text_core_persistent(
        CampaignRequest(goal="Criar campanha persistente de teste"),
        store=store,
        runner=runner,
    )

    assert result.result.publication_authorized is False
    assert result.resume_state.run_status == "completed"
    assert result.resume_state.current_stage == "human_approval"
    assert result.resume_state.completed_sequences == [0, 1, 2]
    assert result.resume_state.unfinished_sequences == []
    assert result.resume_state.checkpoint_key == "text_core_complete"
    assert [event["event_type"] for event in store.events] == [
        "run.created",
        "task.started",
        "task.completed",
        "task.started",
        "task.completed",
        "task.started",
        "task.completed",
        "run.completed",
    ]


def test_memory_upsert_and_read_isolated_by_scope():
    store = InMemoryMemoryStore()
    store.save_memory(
        scope="project:integrasquad",
        key="brand",
        content={"tone": "humano"},
    )
    store.save_memory(
        scope="project:other",
        key="brand",
        content={"tone": "formal"},
    )

    assert store.get_memory(scope="project:integrasquad", key="brand") == {"tone": "humano"}
    assert store.get_memory(scope="project:missing", key="brand") is None


def test_failure_persists_failed_run_and_task():
    store = InMemoryMemoryStore()

    def runner(agent, prompt):
        raise ValueError("falha controlada")

    with pytest.raises(ValueError, match="falha controlada"):
        run_text_core_persistent(
            CampaignRequest(goal="Criar campanha que falha no teste"),
            store=store,
            runner=runner,
        )

    run = next(iter(store.runs.values()))
    tasks = sorted(store.tasks.values(), key=lambda item: item["sequence"])
    assert run["status"] == "failed"
    assert tasks[0]["status"] == "failed"
    assert tasks[1]["status"] == "pending"
    assert tasks[2]["status"] == "pending"
