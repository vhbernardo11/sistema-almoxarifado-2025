from __future__ import annotations

import unicodedata

from .models import ExcludeAutoWorkKind, MaestroPlan, PlanStep, WorkRequest
from .registry import get_specialist

ROUTES: dict[ExcludeAutoWorkKind, tuple[str, ...]] = {
    "campaign": ("researcher", "strategist", "copywriter", "reviewer"),
    "software": ("researcher", "programmer", "tester", "reviewer"),
    "commercial": ("researcher", "commercial", "copywriter", "reviewer"),
    "legal": ("researcher", "legal_reviewer", "reviewer"),
    "seo": ("researcher", "seo_analyst", "copywriter", "reviewer"),
    "analytics": ("analytics", "strategist", "reviewer"),
    "operations": ("strategist", "reviewer"),
}

_KEYWORDS: list[tuple[ExcludeAutoWorkKind, tuple[str, ...]]] = [
    ("legal", ("contrato", "juridico", "juridica", "lei", "clausula", "processo legal")),
    ("software", ("sistema", "aplicativo", " app ", "codigo", "bug", "site", "api", "banco de dados", "integracao", "programar")),
    ("commercial", ("venda", "cliente", "lead", "prospeccao", "proposta comercial", "preco", "orcamento")),
    ("seo", (" seo ", "google", "palavra-chave", "palavras-chave", "ranking", "busca organica")),
    ("analytics", ("metrica", "metricas", "dashboard", "conversao", "funil", "dados", "relatorio")),
    ("campaign", ("campanha", "instagram", "reels", "anuncio", "copy", "post", "marketing", "conteudo")),
]

_STEP_OBJECTIVES = {
    "researcher": "Levantar fatos, contexto, riscos e fontes relevantes para o pedido.",
    "strategist": "Definir a estratégia e os guardrails a partir do contexto disponível.",
    "copywriter": "Produzir a redação necessária respeitando estratégia e fatos validados.",
    "reviewer": "Revisar consistência, riscos, critérios de aceite e necessidade de aprovação humana.",
    "programmer": "Projetar e implementar a solução de software dentro do escopo aprovado.",
    "tester": "Validar a implementação com testes e critérios de aceite reproduzíveis.",
    "commercial": "Estruturar a abordagem comercial, oferta, objeções e próximos passos.",
    "legal_reviewer": "Identificar riscos jurídicos, lacunas e pontos para validação humana especializada.",
    "seo_analyst": "Estruturar intenção de busca, tópicos e oportunidades de SEO.",
    "analytics": "Interpretar dados e métricas disponíveis para gerar diagnóstico acionável.",
}


def _normalize(value: str) -> str:
    plain = "".join(
        char for char in unicodedata.normalize("NFKD", value.lower())
        if not unicodedata.combining(char)
    )
    return f" {plain} "


def infer_work_kind(objective: str) -> ExcludeAutoWorkKind:
    normalized = _normalize(objective)
    for kind, keywords in _KEYWORDS:
        if any(keyword in normalized for keyword in keywords):
            return kind
    return "operations"


def plan_work(request: WorkRequest) -> MaestroPlan:
    route: ExcludeAutoWorkKind
    if request.kind == "auto":
        route = infer_work_kind(request.objective)
    else:
        route = request.kind

    steps: list[PlanStep] = []
    blockers: list[str] = []
    for sequence, specialist_id in enumerate(ROUTES[route]):
        specialist = get_specialist(specialist_id)
        executable = specialist.state == "implemented" and specialist.external_effect != "publish"
        if not executable:
            blockers.append(
                f"{specialist.name}: capacidade {specialist.state}; executor especializado ainda não está liberado."
            )
        steps.append(
            PlanStep(
                sequence=sequence,
                specialist_id=specialist.id,
                specialist_name=specialist.name,
                objective=_STEP_OBJECTIVES[specialist.id],
                state=specialist.state,
                executable=executable,
                external_effect=specialist.external_effect,
                depends_on=([sequence - 1] if sequence > 0 else []),
            )
        )

    # A Etapa 11 é deliberadamente fail-closed para qualquer efeito externo.
    # `allow_external_actions` fica registrado no pedido, mas não autoriza Publisher.
    return MaestroPlan(
        request=request,
        route=route,
        steps=steps,
        ready_for_execution=not blockers,
        blockers=blockers,
        publication_authorized=False,
        external_actions_authorized=False,
    )
