from __future__ import annotations

from .models import SpecialistSpec


SPECIALISTS: dict[str, SpecialistSpec] = {
    "researcher": SpecialistSpec(
        id="researcher",
        name="Researcher",
        purpose="Pesquisar fatos, contexto, riscos e fontes confiáveis.",
        state="implemented",
        external_effect="read",
        notes="Busca web existe no núcleo textual; execução ao vivo continua dependente de credencial do runtime.",
    ),
    "strategist": SpecialistSpec(
        id="strategist",
        name="Strategist",
        purpose="Transformar evidências em estratégia, posicionamento e guardrails.",
        state="implemented",
    ),
    "copywriter": SpecialistSpec(
        id="copywriter",
        name="Copywriter",
        purpose="Produzir texto final sem inventar provas ou autorizar publicação.",
        state="implemented",
    ),
    "reviewer": SpecialistSpec(
        id="reviewer",
        name="Reviewer",
        purpose="Revisar consistência, riscos e aderência aos guardrails antes de aprovação humana.",
        state="implemented",
    ),
    "programmer": SpecialistSpec(
        id="programmer",
        name="Programmer",
        purpose="Projetar e implementar mudanças de software com escopo controlado.",
        state="prepared",
        notes="Contrato de papel pronto; executor especializado será conectado em etapa posterior.",
    ),
    "tester": SpecialistSpec(
        id="tester",
        name="Tester",
        purpose="Validar comportamento, regressões, falhas e critérios de aceite.",
        state="prepared",
    ),
    "commercial": SpecialistSpec(
        id="commercial",
        name="Commercial",
        purpose="Estruturar oferta, prospecção, objeções e materiais comerciais.",
        state="prepared",
    ),
    "legal_reviewer": SpecialistSpec(
        id="legal_reviewer",
        name="Legal Reviewer",
        purpose="Sinalizar riscos jurídicos e pontos que exigem validação humana especializada.",
        state="prepared",
        notes="Não substitui advogado e não toma decisões jurídicas finais.",
    ),
    "seo_analyst": SpecialistSpec(
        id="seo_analyst",
        name="SEO Analyst",
        purpose="Planejar intenção de busca, tópicos, palavras-chave e estrutura de conteúdo.",
        state="prepared",
    ),
    "analytics": SpecialistSpec(
        id="analytics",
        name="Analytics",
        purpose="Interpretar métricas, funis e sinais operacionais para apoiar decisões.",
        state="prepared",
        external_effect="read",
    ),
    "publisher": SpecialistSpec(
        id="publisher",
        name="Publisher",
        purpose="Executar publicação externa somente após aprovação humana e autorização explícita.",
        state="implemented",
        external_effect="publish",
        approval_required=True,
        notes="Nunca participa de rotas automáticas do Maestro.",
    ),
}


def get_specialist(specialist_id: str) -> SpecialistSpec:
    try:
        return SPECIALISTS[specialist_id]
    except KeyError as exc:
        raise KeyError(f"Especialista desconhecido: {specialist_id}") from exc
