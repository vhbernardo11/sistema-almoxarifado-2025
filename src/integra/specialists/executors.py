from __future__ import annotations

import ast
import json
import re
import unicodedata
from collections.abc import Callable
from typing import Any

from .models import SpecialistExecutionError, SpecialistResult, SpecialistTask


def _safe_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip()
    if not normalized or normalized.startswith("/") or normalized.startswith("../") or "/../" in normalized:
        raise SpecialistExecutionError(f"Caminho de workspace inválido: {path}")
    return normalized


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SpecialistExecutionError(f"Campo obrigatório ausente ou inválido: {field}")
    return value.strip()


def execute_programmer(task: SpecialistTask) -> SpecialistResult:
    workspace_raw = task.payload.get("workspace", {})
    operations = task.payload.get("operations", [])
    if not isinstance(workspace_raw, dict) or not isinstance(operations, list):
        raise SpecialistExecutionError("Programmer exige workspace=dict e operations=list.")

    workspace = {_safe_path(str(path)): str(content) for path, content in workspace_raw.items()}
    changed: list[dict[str, Any]] = []

    for index, operation in enumerate(operations):
        if not isinstance(operation, dict):
            raise SpecialistExecutionError(f"Operação {index} deve ser objeto.")
        action = operation.get("action")
        path = _safe_path(_text(operation.get("path"), f"operations[{index}].path"))

        if action == "write_file":
            content = str(operation.get("content", ""))
            existed = path in workspace
            workspace[path] = content
            changed.append({"path": path, "action": "updated" if existed else "created"})
        elif action == "append_text":
            content = str(operation.get("content", ""))
            workspace[path] = workspace.get(path, "") + content
            changed.append({"path": path, "action": "appended"})
        elif action == "replace_text":
            if path not in workspace:
                raise SpecialistExecutionError(f"Arquivo não existe para replace_text: {path}")
            old = _text(operation.get("old"), f"operations[{index}].old")
            new = str(operation.get("new", ""))
            count = int(operation.get("count", 0))
            if old not in workspace[path]:
                raise SpecialistExecutionError(f"Trecho não encontrado em {path}")
            workspace[path] = workspace[path].replace(old, new, count if count > 0 else -1)
            changed.append({"path": path, "action": "replaced"})
        elif action == "delete_file":
            if path not in workspace:
                raise SpecialistExecutionError(f"Arquivo não existe para delete_file: {path}")
            del workspace[path]
            changed.append({"path": path, "action": "deleted"})
        else:
            raise SpecialistExecutionError(f"Ação de Programmer não permitida: {action}")

    return SpecialistResult(
        specialist_id="programmer",
        actor_id=task.actor_id,
        status="completed",
        data={
            "workspace": workspace,
            "changed_files": changed,
            "operation_count": len(operations),
        },
    )


def _run_check(workspace: dict[str, str], check: dict[str, Any]) -> dict[str, Any]:
    kind = check.get("kind")
    path = _safe_path(_text(check.get("path"), "check.path"))
    content = workspace.get(path)
    passed = False
    detail = ""

    if kind == "file_exists":
        passed = path in workspace
        detail = "arquivo presente" if passed else "arquivo ausente"
    elif kind == "file_not_exists":
        passed = path not in workspace
        detail = "arquivo ausente" if passed else "arquivo ainda presente"
    elif kind in {"contains", "not_contains"}:
        needle = _text(check.get("value"), "check.value")
        if content is None:
            passed = False
            detail = "arquivo ausente"
        else:
            contains = needle in content
            passed = contains if kind == "contains" else not contains
            detail = f"trecho {'encontrado' if contains else 'não encontrado'}"
    elif kind == "json_valid":
        try:
            if content is None:
                raise ValueError("arquivo ausente")
            json.loads(content)
            passed = True
            detail = "JSON válido"
        except Exception as exc:  # noqa: BLE001 - resultado do teste
            detail = f"JSON inválido: {exc}"
    elif kind == "python_compile":
        try:
            if content is None:
                raise ValueError("arquivo ausente")
            ast.parse(content, filename=path)
            passed = True
            detail = "Python sintaticamente válido"
        except Exception as exc:  # noqa: BLE001 - resultado do teste
            detail = f"Python inválido: {exc}"
    else:
        raise SpecialistExecutionError(f"Tipo de teste não permitido: {kind}")

    return {"kind": kind, "path": path, "passed": passed, "detail": detail}


def execute_tester(task: SpecialistTask) -> SpecialistResult:
    workspace_raw = task.payload.get("workspace", {})
    checks = task.payload.get("checks", [])
    if not isinstance(workspace_raw, dict) or not isinstance(checks, list):
        raise SpecialistExecutionError("Tester exige workspace=dict e checks=list.")
    workspace = {_safe_path(str(path)): str(content) for path, content in workspace_raw.items()}
    results = [_run_check(workspace, check) for check in checks]
    passed = bool(results) and all(item["passed"] for item in results)
    return SpecialistResult(
        specialist_id="tester",
        actor_id=task.actor_id,
        status="completed" if passed else "needs_review",
        data={"passed": passed, "checks": results, "check_count": len(results)},
        warnings=[] if passed else ["Um ou mais critérios de teste falharam."],
        requires_human_review=not passed,
    )


def execute_commercial(task: SpecialistTask) -> SpecialistResult:
    offer = _text(task.payload.get("offer_name"), "offer_name")
    audience = _text(task.payload.get("audience"), "audience")
    cta = _text(task.payload.get("cta"), "cta")
    benefits = [str(item).strip() for item in task.payload.get("benefits", []) if str(item).strip()]
    proofs = [str(item).strip() for item in task.payload.get("proofs", []) if str(item).strip()]
    if not benefits:
        raise SpecialistExecutionError("Commercial exige ao menos um benefício informado.")

    value = f"{offer} ajuda {audience} a {benefits[0].rstrip('.').lower()}."
    script = [
        f"Olá! Estou entrando em contato sobre {offer}.",
        f"Para {audience}, a proposta é: {benefits[0].rstrip('.')}.",
    ]
    if len(benefits) > 1:
        script.append("Outros pontos: " + "; ".join(benefits[1:3]) + ".")
    if proofs:
        script.append("Base disponível: " + "; ".join(proofs[:2]) + ".")
    script.append(cta)

    warnings: list[str] = []
    if not proofs:
        warnings.append("Nenhuma prova foi fornecida; o material não inventa resultados, números ou depoimentos.")

    return SpecialistResult(
        specialist_id="commercial",
        actor_id=task.actor_id,
        status="completed",
        data={
            "value_proposition": value,
            "outreach_script": " ".join(script),
            "objection_prompts": [
                "Qual é a principal dúvida sobre custo?",
                "Qual é a principal dúvida sobre tempo para começar?",
                "Que evidência real pode aumentar confiança sem inventar promessa?",
            ],
            "facts_used": {"benefits": benefits, "proofs": proofs},
        },
        warnings=warnings,
    )


_LEGAL_RULES: tuple[tuple[str, str, str], ...] = (
    ("exclusividade", r"\bexclusiv\w*", "Cláusula de exclusividade merece revisão de alcance e duração."),
    ("multa", r"\bmulta\w*|penalidade", "Há referência a multa ou penalidade; revisar proporcionalidade e gatilhos."),
    ("renovacao", r"renova[cç][aã]o\s+autom[aá]tica", "Renovação automática exige atenção a aviso, prazo e cancelamento."),
    ("rescisao", r"rescis[aã]o|rescind", "Há termos de rescisão; conferir hipóteses, prazo e efeitos."),
    ("foro", r"\bforo\b", "Há eleição de foro; validar adequação com profissional jurídico."),
    ("dados_pessoais", r"dados\s+pessoais|lgpd|privacidade", "Há tratamento de dados pessoais; revisar obrigações de privacidade/LGPD."),
    ("garantia", r"garantia\s+(?:total|absoluta|integral)|garantimos", "Linguagem de garantia pode criar obrigação ampla ou promessa de resultado."),
    ("irrevogavel", r"irrevog[aá]vel|irretrat[aá]vel", "Termo de irrevogabilidade/irretratabilidade exige revisão especializada."),
)


def execute_legal(task: SpecialistTask) -> SpecialistResult:
    text = _text(task.payload.get("text"), "text")
    flags: list[dict[str, str]] = []
    for code, pattern, note in _LEGAL_RULES:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            start = max(0, match.start() - 45)
            end = min(len(text), match.end() + 70)
            flags.append({"code": code, "note": note, "snippet": text[start:end].strip()})

    warnings = [
        "Triagem automatizada: não substitui advogado nem valida legalidade, validade ou exigibilidade do documento."
    ]
    if not flags:
        warnings.append("Nenhum padrão da lista de triagem foi detectado; isso não significa ausência de risco jurídico.")

    return SpecialistResult(
        specialist_id="legal_reviewer",
        actor_id=task.actor_id,
        status="needs_review",
        data={
            "jurisdiction": task.payload.get("jurisdiction"),
            "risk_flags": flags,
            "flag_count": len(flags),
        },
        warnings=warnings,
        requires_human_review=True,
    )


def _slug(value: str) -> str:
    plain = "".join(
        char for char in unicodedata.normalize("NFKD", value.lower())
        if not unicodedata.combining(char)
    )
    plain = re.sub(r"[^a-z0-9]+", "-", plain).strip("-")
    return plain[:80]


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: max(1, limit - 1)].rstrip(" ,.;:-") + "…"


def execute_seo(task: SpecialistTask) -> SpecialistResult:
    topic = _text(task.payload.get("topic"), "topic")
    primary = _text(task.payload.get("primary_keyword"), "primary_keyword")
    secondaries = [str(item).strip() for item in task.payload.get("secondary_keywords", []) if str(item).strip()]
    brand = str(task.payload.get("brand", "")).strip()
    city = str(task.payload.get("city", "")).strip()

    title_base = f"{topic}: {primary}"
    if brand:
        title_base += f" | {brand}"
    meta = f"Entenda {primary} em {topic}."
    if city:
        meta += f" Conteúdo voltado para {city}."
    meta += " Veja pontos principais e próximos passos."

    outline = [f"O que é {primary}", f"Como {primary} se aplica a {topic}"]
    outline.extend(f"{keyword}: pontos importantes" for keyword in secondaries[:4])

    return SpecialistResult(
        specialist_id="seo_analyst",
        actor_id=task.actor_id,
        status="completed",
        data={
            "slug": _slug(primary + (f" {city}" if city else "")),
            "title": _truncate(title_base, 60),
            "meta_description": _truncate(meta, 155),
            "h1": topic,
            "outline_h2": outline,
            "keywords": {"primary": primary, "secondary": secondaries},
        },
    )


def _number_map(value: Any, field: str) -> dict[str, float]:
    if not isinstance(value, dict):
        raise SpecialistExecutionError(f"{field} deve ser um objeto de métricas numéricas.")
    result: dict[str, float] = {}
    for key, item in value.items():
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise SpecialistExecutionError(f"Métrica não numérica em {field}.{key}")
        result[str(key)] = float(item)
    return result


def _rate(numerator: float, denominator: float) -> float | None:
    return None if denominator == 0 else round((numerator / denominator) * 100, 2)


def execute_analytics(task: SpecialistTask) -> SpecialistResult:
    current = _number_map(task.payload.get("current", {}), "current")
    previous = _number_map(task.payload.get("previous", {}), "previous")
    if not current:
        raise SpecialistExecutionError("Analytics exige ao menos uma métrica atual.")

    deltas: dict[str, dict[str, float | None]] = {}
    alerts: list[str] = []
    for key, value in current.items():
        if key not in previous:
            continue
        before = previous[key]
        pct = None if before == 0 else round(((value - before) / before) * 100, 2)
        deltas[key] = {"absolute": round(value - before, 4), "percent": pct}
        if pct is not None and pct <= -20:
            alerts.append(f"{key} caiu {abs(pct):.2f}% versus período anterior.")

    funnel: dict[str, float | None] = {}
    if "visits" in current and "leads" in current:
        funnel["visit_to_lead_percent"] = _rate(current["leads"], current["visits"])
    if "leads" in current and "conversions" in current:
        funnel["lead_to_conversion_percent"] = _rate(current["conversions"], current["leads"])
    if "conversions" in current and "revenue" in current:
        funnel["revenue_per_conversion"] = None if current["conversions"] == 0 else round(
            current["revenue"] / current["conversions"], 2
        )

    return SpecialistResult(
        specialist_id="analytics",
        actor_id=task.actor_id,
        status="completed",
        data={"current": current, "previous": previous, "deltas": deltas, "funnel": funnel, "alerts": alerts},
        warnings=["Métricas são calculadas apenas a partir dos valores fornecidos; nenhuma fonte externa foi consultada."],
    )


EXECUTORS: dict[str, Callable[[SpecialistTask], SpecialistResult]] = {
    "programmer": execute_programmer,
    "tester": execute_tester,
    "commercial": execute_commercial,
    "legal_reviewer": execute_legal,
    "seo_analyst": execute_seo,
    "analytics": execute_analytics,
}
