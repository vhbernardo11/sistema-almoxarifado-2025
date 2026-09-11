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
        purpose="Aplicar mudanças declarativas em workspace virtual, com escopo controlado e sem efeito externo.",
        state="implemented",
        notes="Executor determinístico da Etapa 12; não deriva código de linguagem natural e não grava em repositórios externos.",
    ),
    "tester": SpecialistSpec(
        id="tester",
        name="Tester",
        purpose="Validar arquivos e critérios reproduzíveis sem executar código arbitrário.",
        state="implemented",
        notes="Suporta presença/ausência, conteúdo, JSON e sintaxe Python em workspace virtual.",
    ),
    "commercial": SpecialistSpec(
        id="commercial",
        name="Commercial",
        purpose="Estruturar proposta e abordagem comercial somente com fatos fornecidos.",
        state="implemented",
        notes="Não envia mensagens nem inventa resultados, provas ou depoimentos.",
    ),
    "legal_reviewer": SpecialistSpec(
        id="legal_reviewer",
        name="Legal Reviewer",
        purpose="Executar triagem determinística de riscos jurídicos e exigir revisão humana.",
        state="implemented",
        notes="Não substitui advogado e nunca emite decisão jurídica final.",
    ),
    "seo_analyst": SpecialistSpec(
        id="seo_analyst",
        name="SEO Analyst",
        purpose="Gerar pacote on-page determinístico a partir de tópico e palavras-chave fornecidos.",
        state="implemented",
        notes="Não consulta ranking, volume ou concorrência externos nesta etapa.",
    ),
    "analytics": SpecialistSpec(
        id="analytics",
        name="Analytics",
        purpose="Calcular deltas, taxas de funil e alertas a partir de métricas fornecidas.",
        state="implemented",
        external_effect="none",
        notes="Não consulta fontes externas e não modifica dados.",
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
