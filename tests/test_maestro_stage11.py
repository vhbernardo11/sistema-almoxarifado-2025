from integra.maestro import ROUTES, SPECIALISTS, WorkRequest, infer_work_kind, plan_work


def test_publisher_exists_but_is_never_in_automatic_routes():
    assert "publisher" in SPECIALISTS
    assert SPECIALISTS["publisher"].external_effect == "publish"
    assert SPECIALISTS["publisher"].approval_required is True
    assert all("publisher" not in route for route in ROUTES.values())


def test_campaign_route_is_ready_and_fail_closed_for_publication():
    plan = plan_work(WorkRequest(objective="Criar uma campanha para o IntegraTrampo no Instagram"))
    assert plan.route == "campaign"
    assert [step.specialist_id for step in plan.steps] == [
        "researcher", "strategist", "copywriter", "reviewer"
    ]
    assert plan.ready_for_execution is True
    assert plan.blockers == []
    assert plan.publication_authorized is False
    assert plan.external_actions_authorized is False
    assert all(step.external_effect != "publish" for step in plan.steps)


def test_software_route_reflects_stage12_specialists_as_implemented():
    plan = plan_work(WorkRequest(objective="Criar um aplicativo para organizar serviços e corrigir bugs"))
    assert plan.route == "software"
    assert [step.specialist_id for step in plan.steps] == [
        "researcher", "programmer", "tester", "reviewer"
    ]
    assert plan.ready_for_execution is True
    assert plan.blockers == []
    assert all(step.executable for step in plan.steps)


def test_auto_inference_handles_accents_and_common_work_types():
    assert infer_work_kind("Revisar cláusula jurídica de contrato") == "legal"
    assert infer_work_kind("Criar integração de API para o sistema") == "software"
    assert infer_work_kind("Montar proposta comercial para novos clientes") == "commercial"
    assert infer_work_kind("Melhorar ranking no Google com SEO") == "seo"
    assert infer_work_kind("Analisar métricas do funil e dashboard") == "analytics"
    assert infer_work_kind("Planejar campanha de conteúdo no Instagram") == "campaign"
    assert infer_work_kind("Organizar prioridades internas da equipe") == "operations"


def test_explicit_route_wins_over_keyword_inference():
    plan = plan_work(WorkRequest(
        objective="Criar campanha sobre um contrato",
        kind="campaign",
    ))
    assert plan.route == "campaign"


def test_external_action_request_does_not_bypass_stage11_gate():
    plan = plan_work(WorkRequest(
        objective="Criar campanha e publicar automaticamente",
        kind="campaign",
        allow_external_actions=True,
    ))
    assert plan.request.allow_external_actions is True
    assert plan.publication_authorized is False
    assert plan.external_actions_authorized is False
    assert "publisher" not in [step.specialist_id for step in plan.steps]


def test_plan_is_sequential_and_reproducible():
    request = WorkRequest(objective="Criar campanha para profissionais locais")
    first = plan_work(request)
    second = plan_work(request)
    assert first == second
    for index, step in enumerate(first.steps):
        assert step.sequence == index
        assert step.depends_on == ([index - 1] if index > 0 else [])
