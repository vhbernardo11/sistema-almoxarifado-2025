import pytest

from integra.maestro import WorkRequest, plan_work
from integra.specialists import SpecialistExecutionError, SpecialistTask, execute_specialist


ACTOR = "stage8-test-user-001"


def test_stage12_blocks_real_users_and_external_authorization():
    with pytest.raises(SpecialistExecutionError):
        execute_specialist(SpecialistTask(
            specialist_id="analytics",
            actor_id="real-user-001",
            objective="Analisar métricas do funil",
            payload={"current": {"visits": 10}},
        ))

    with pytest.raises(SpecialistExecutionError):
        execute_specialist(SpecialistTask(
            specialist_id="analytics",
            actor_id=ACTOR,
            objective="Analisar métricas do funil",
            payload={"current": {"visits": 10}},
            external_actions_authorized=True,
        ))


def test_programmer_applies_only_declarative_changes_in_virtual_workspace():
    result = execute_specialist(SpecialistTask(
        specialist_id="programmer",
        actor_id=ACTOR,
        objective="Atualizar arquivo de configuração sintético",
        payload={
            "workspace": {"app.py": "MODE = 'old'\n"},
            "operations": [
                {"action": "replace_text", "path": "app.py", "old": "old", "new": "test"},
                {"action": "write_file", "path": "settings.json", "content": "{\"enabled\": true}"},
            ],
        },
    ))
    assert result.status == "completed"
    assert result.data["workspace"]["app.py"] == "MODE = 'test'\n"
    assert result.data["workspace"]["settings.json"] == '{"enabled": true}'
    assert result.external_actions_authorized is False
    assert result.publication_authorized is False


def test_tester_validates_python_json_and_content_without_executing_code():
    result = execute_specialist(SpecialistTask(
        specialist_id="tester",
        actor_id=ACTOR,
        objective="Validar workspace sintético",
        payload={
            "workspace": {
                "app.py": "value = 42\n",
                "settings.json": "{\"enabled\": true}",
            },
            "checks": [
                {"kind": "python_compile", "path": "app.py"},
                {"kind": "contains", "path": "app.py", "value": "42"},
                {"kind": "json_valid", "path": "settings.json"},
            ],
        },
    ))
    assert result.data["passed"] is True
    assert all(item["passed"] for item in result.data["checks"])


def test_commercial_uses_only_supplied_benefits_and_flags_missing_proof():
    result = execute_specialist(SpecialistTask(
        specialist_id="commercial",
        actor_id=ACTOR,
        objective="Criar abordagem comercial de teste",
        payload={
            "offer_name": "IntegraTrampo Teste",
            "audience": "profissionais autônomos de teste",
            "benefits": ["organizar oportunidades em um só lugar"],
            "cta": "Cadastre o perfil de teste para avaliar o fluxo.",
            "proofs": [],
        },
    ))
    assert "organizar oportunidades" in result.data["value_proposition"]
    assert result.warnings
    assert "resultados" not in result.data["outreach_script"].lower()


def test_legal_reviewer_always_requires_human_review_and_flags_patterns():
    result = execute_specialist(SpecialistTask(
        specialist_id="legal_reviewer",
        actor_id=ACTOR,
        objective="Fazer triagem jurídica sintética",
        payload={
            "text": "O contrato prevê exclusividade, multa, renovação automática e tratamento de dados pessoais.",
            "jurisdiction": "BR",
        },
    ))
    codes = {item["code"] for item in result.data["risk_flags"]}
    assert {"exclusividade", "multa", "renovacao", "dados_pessoais"}.issubset(codes)
    assert result.status == "needs_review"
    assert result.requires_human_review is True


def test_seo_builds_deterministic_on_page_pack():
    result = execute_specialist(SpecialistTask(
        specialist_id="seo_analyst",
        actor_id=ACTOR,
        objective="Gerar pacote SEO sintético",
        payload={
            "topic": "Serviços de eletricista",
            "primary_keyword": "eletricista em Teodoro Sampaio",
            "secondary_keywords": ["instalação elétrica", "manutenção elétrica"],
            "brand": "IntegraTrampo Teste",
            "city": "Teodoro Sampaio",
        },
    ))
    assert result.data["slug"] == "eletricista-em-teodoro-sampaio-teodoro-sampaio"
    assert len(result.data["title"]) <= 60
    assert len(result.data["meta_description"]) <= 155
    assert result.data["keywords"]["primary"] == "eletricista em Teodoro Sampaio"


def test_analytics_calculates_funnel_and_period_delta():
    result = execute_specialist(SpecialistTask(
        specialist_id="analytics",
        actor_id=ACTOR,
        objective="Analisar funil de teste",
        payload={
            "current": {"visits": 1000, "leads": 100, "conversions": 20, "revenue": 2000},
            "previous": {"visits": 800, "leads": 125, "conversions": 25, "revenue": 2500},
        },
    ))
    assert result.data["funnel"]["visit_to_lead_percent"] == 10.0
    assert result.data["funnel"]["lead_to_conversion_percent"] == 20.0
    assert result.data["funnel"]["revenue_per_conversion"] == 100.0
    assert result.data["deltas"]["visits"]["percent"] == 25.0
    assert any("leads caiu" in item for item in result.data["alerts"])


def test_maestro_routes_become_structurally_ready_after_stage12():
    for kind, objective in [
        ("software", "Criar sistema de teste"),
        ("commercial", "Montar proposta comercial de teste"),
        ("legal", "Revisar contrato jurídico de teste"),
        ("seo", "Planejar SEO de teste"),
        ("analytics", "Analisar métricas de teste"),
    ]:
        plan = plan_work(WorkRequest(objective=objective, kind=kind))
        assert plan.ready_for_execution is True
        assert plan.blockers == []
        assert plan.publication_authorized is False
        assert plan.external_actions_authorized is False
