from __future__ import annotations

from types import SimpleNamespace

import pytest

from integra.text_core.agents import build_copywriter, build_researcher, build_strategist
from integra.text_core.models import (
    CampaignRequest,
    CopyPackage,
    ResearchBrief,
    ResearchSource,
    StrategyBrief,
)
from integra.text_core.workflow import run_text_core


def sample_research() -> ResearchBrief:
    return ResearchBrief(
        objective="Atrair profissionais para conhecer a plataforma",
        audience_insights=["Profissionais valorizam oportunidades claras e locais"],
        market_context=["Mensagem deve explicar a proposta sem prometer renda garantida"],
        opportunities=["Destacar conexão entre demanda e profissionais"],
        risks=["Evitar promessa de contratação ou renda"],
        facts_to_use=["A proposta da campanha é apresentar uma plataforma de conexão"],
        sources=[
            ResearchSource(
                title="Fonte de teste",
                url="https://example.org/source",
                note="Fonte sintética usada apenas no teste unitário",
            )
        ],
        confidence="medium",
    )


def sample_strategy() -> StrategyBrief:
    return StrategyBrief(
        objective="Gerar interesse qualificado",
        positioning="Ponte entre quem precisa e quem sabe fazer",
        core_message="Novas conexões podem começar pelo IntegraTrampo",
        promise="Facilitar a descoberta de oportunidades e profissionais",
        proof_points=["Fluxo de conexão simples"],
        objections=["Não é promessa de contratação"],
        content_angle="Oportunidade de ser encontrado",
        call_to_action="Conheça o IntegraTrampo",
        guardrails=["Não prometer renda", "Não inventar números"],
    )


def sample_copy() -> CopyPackage:
    return CopyPackage(
        headline="Seu próximo contato pode começar aqui",
        primary_copy="O IntegraTrampo aproxima quem precisa de um serviço de quem sabe fazer.",
        short_caption="Mostre seu trabalho. Crie novas conexões.",
        long_caption="Conheça uma forma simples de aproximar demanda e profissionais, sem promessas irreais.",
        call_to_action="Conheça o IntegraTrampo",
        hashtags=["#IntegraTrampo"],
        visual_brief="Profissional real em contexto de trabalho, interface limpa e CTA visível.",
        claims_used=["A campanha apresenta uma plataforma de conexão"],
    )


def test_agents_have_structured_outputs_and_only_researcher_has_web_tool():
    researcher = build_researcher()
    strategist = build_strategist()
    copywriter = build_copywriter()

    assert researcher.output_type is ResearchBrief
    assert strategist.output_type is StrategyBrief
    assert copywriter.output_type is CopyPackage
    assert len(researcher.tools) == 1
    assert strategist.tools == []
    assert copywriter.tools == []


def test_text_core_chains_all_three_agents_and_never_authorizes_publication():
    outputs = [sample_research(), sample_strategy(), sample_copy()]
    prompts: list[str] = []

    def fake_runner(agent, prompt):
        prompts.append(prompt)
        return SimpleNamespace(final_output=outputs[len(prompts) - 1])

    request = CampaignRequest(
        goal="Criar campanha para apresentar o IntegraTrampo a eletricistas",
        audience="Eletricistas autônomos",
        location="Teodoro Sampaio, SP",
    )

    result = run_text_core(request, runner=fake_runner)

    assert len(prompts) == 3
    assert "PEDIDO ORIGINAL" in prompts[0]
    assert "RESEARCH BRIEF" in prompts[1]
    assert "Fonte de teste" in prompts[1]
    assert "STRATEGY BRIEF" in prompts[2]
    assert "Não prometer renda" in prompts[2]
    assert result.research == outputs[0]
    assert result.strategy == outputs[1]
    assert result.copy == outputs[2]
    assert result.publication_authorized is False


def test_live_text_core_fails_closed_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    request = CampaignRequest(goal="Criar uma campanha textual de teste para o IntegraTrampo")

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        run_text_core(request)
