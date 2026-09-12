from __future__ import annotations

from typing import Any, Callable

from .models import SpecialistExecutionError, SpecialistResult, SpecialistTask


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SpecialistExecutionError(f"Campo obrigatório ausente ou inválido: {field}")
    return value.strip()


def _strings(value: Any, field: str, *, required: bool = False) -> list[str]:
    if value is None:
        items: list[str] = []
    elif isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
    else:
        raise SpecialistExecutionError(f"{field} deve ser uma lista.")
    if required and not items:
        raise SpecialistExecutionError(f"{field} exige ao menos um item.")
    return items


def execute_researcher(task: SpecialistTask) -> SpecialistResult:
    facts = _strings(task.payload.get("facts"), "facts", required=True)
    questions = _strings(task.payload.get("questions"), "questions")
    sources_raw = task.payload.get("sources", [])
    if not isinstance(sources_raw, list):
        raise SpecialistExecutionError("sources deve ser uma lista.")
    sources: list[dict[str, str]] = []
    for index, item in enumerate(sources_raw):
        if not isinstance(item, dict):
            raise SpecialistExecutionError(f"sources[{index}] deve ser objeto.")
        label = _text(item.get("label"), f"sources[{index}].label")
        url = str(item.get("url", "")).strip()
        sources.append({"label": label, "url": url})

    gaps = questions or ["Nenhuma pergunta de pesquisa adicional foi fornecida."]
    return SpecialistResult(
        specialist_id="researcher",
        actor_id=task.actor_id,
        status="completed",
        data={
            "facts": facts,
            "sources": sources,
            "open_questions": gaps,
            "external_research_performed": False,
        },
        warnings=[
            "Researcher da Etapa 14 opera somente sobre fatos e fontes fornecidos no payload; não faz busca externa."
        ],
    )


def execute_strategist(task: SpecialistTask) -> SpecialistResult:
    goal = _text(task.payload.get("goal"), "goal")
    audience = _text(task.payload.get("audience"), "audience")
    facts = _strings(task.payload.get("facts"), "facts")
    constraints = _strings(task.payload.get("constraints"), "constraints")
    priorities = _strings(task.payload.get("priorities"), "priorities")
    if not priorities:
        priorities = [
            "Manter a proposta aderente ao objetivo informado.",
            "Não inventar resultados, números ou provas.",
            "Preservar revisão humana antes de qualquer efeito externo.",
        ]

    return SpecialistResult(
        specialist_id="strategist",
        actor_id=task.actor_id,
        status="completed",
        data={
            "goal": goal,
            "audience": audience,
            "strategy_statement": f"Para {audience}, orientar o trabalho para {goal.rstrip('.').lower()}.",
            "priorities": priorities,
            "constraints": constraints,
            "facts_used": facts,
            "guardrails": [
                "Sem publicação automática.",
                "Sem promessa não sustentada pelos fatos fornecidos.",
                "Sem efeitos externos durante homologação.",
            ],
        },
    )


def execute_copywriter(task: SpecialistTask) -> SpecialistResult:
    headline = _text(task.payload.get("headline"), "headline")
    cta = _text(task.payload.get("cta"), "cta")
    body_points = _strings(task.payload.get("body_points"), "body_points", required=True)
    facts = _strings(task.payload.get("facts"), "facts")
    caption = " ".join(point.rstrip(". ") + "." for point in body_points)
    caption = f"{caption} {cta}".strip()

    return SpecialistResult(
        specialist_id="copywriter",
        actor_id=task.actor_id,
        status="completed",
        data={
            "headline": headline,
            "short_caption": caption,
            "call_to_action": cta,
            "facts_used": facts,
        },
        warnings=[] if facts else [
            "Nenhum fato verificável foi anexado; a copy foi limitada aos pontos explicitamente fornecidos."
        ],
    )


def execute_reviewer(task: SpecialistTask) -> SpecialistResult:
    artifact = task.payload.get("artifact")
    if not isinstance(artifact, dict):
        raise SpecialistExecutionError("Reviewer exige artifact=dict.")
    required_fields = _strings(task.payload.get("required_fields"), "required_fields")
    known_warnings = _strings(task.payload.get("warnings"), "warnings")
    missing = [field for field in required_fields if not artifact.get(field)]

    violations: list[str] = []
    if artifact.get("publication_authorized") is True:
        violations.append("artifact tentou autorizar publicação")
    if artifact.get("external_actions_authorized") is True:
        violations.append("artifact tentou autorizar efeito externo")
    if missing:
        violations.append("campos obrigatórios ausentes: " + ", ".join(missing))

    warnings = known_warnings + violations
    return SpecialistResult(
        specialist_id="reviewer",
        actor_id=task.actor_id,
        status="needs_review",
        data={
            "artifact": artifact,
            "missing_fields": missing,
            "violations": violations,
            "ready_for_human_review": not violations,
        },
        warnings=warnings,
        requires_human_review=True,
    )


STAGE14_EXECUTORS: dict[str, Callable[[SpecialistTask], SpecialistResult]] = {
    "researcher": execute_researcher,
    "strategist": execute_strategist,
    "copywriter": execute_copywriter,
    "reviewer": execute_reviewer,
}
