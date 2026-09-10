from __future__ import annotations

import json
import os
from collections.abc import Callable
from typing import Any, TypeVar

from .agents import build_copywriter, build_researcher, build_strategist
from .models import CampaignRequest, CopyPackage, ResearchBrief, StrategyBrief, TextCoreResult

T = TypeVar("T")
RunnerFn = Callable[[Any, str], Any]


def _coerce_output(value: Any, model_type: type[T]) -> T:
    if isinstance(value, model_type):
        return value
    if isinstance(value, str):
        return model_type.model_validate_json(value)  # type: ignore[attr-defined]
    return model_type.model_validate(value)  # type: ignore[attr-defined]


def _default_runner(agent: Any, prompt: str) -> Any:
    from agents import Runner

    return Runner.run_sync(agent, prompt)


def run_text_core(
    request: CampaignRequest,
    *,
    runner: RunnerFn | None = None,
) -> TextCoreResult:
    """Executa Researcher -> Strategist -> Copywriter.

    O runner pode ser injetado nos testes. Em produção, a execução usa
    OpenAI Agents SDK e exige OPENAI_API_KEY no ambiente.
    """

    if runner is None:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError(
                "OPENAI_API_KEY não está disponível no ambiente. "
                "Configure a chave fora do Git antes de executar o núcleo textual."
            )
        runner = _default_runner

    request_json = request.model_dump_json(indent=2)

    research_run = runner(
        build_researcher(),
        "PEDIDO ORIGINAL:\n" + request_json,
    )
    research = _coerce_output(research_run.final_output, ResearchBrief)

    strategy_prompt = (
        "PEDIDO ORIGINAL:\n"
        + request_json
        + "\n\nRESEARCH BRIEF:\n"
        + research.model_dump_json(indent=2)
    )
    strategy_run = runner(build_strategist(), strategy_prompt)
    strategy = _coerce_output(strategy_run.final_output, StrategyBrief)

    copy_prompt = (
        "PEDIDO ORIGINAL:\n"
        + request_json
        + "\n\nRESEARCH BRIEF:\n"
        + research.model_dump_json(indent=2)
        + "\n\nSTRATEGY BRIEF:\n"
        + strategy.model_dump_json(indent=2)
    )
    copy_run = runner(build_copywriter(), copy_prompt)
    copy = _coerce_output(copy_run.final_output, CopyPackage)

    return TextCoreResult(
        request=request,
        research=research,
        strategy=strategy,
        copy=copy,
        publication_authorized=False,
    )


def result_as_json(result: TextCoreResult) -> str:
    return json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2)
