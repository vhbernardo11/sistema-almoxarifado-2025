from __future__ import annotations

import json
import os
from collections.abc import Callable
from typing import Any, Protocol, TypeVar

from .agents import build_copywriter, build_researcher, build_strategist
from .models import CampaignRequest, CopyPackage, ResearchBrief, StrategyBrief, TextCoreResult

T = TypeVar("T")
RunnerFn = Callable[[Any, str], Any]


class TextCoreObserver(Protocol):
    """Hooks opcionais usados pela camada de persistência sem acoplar o núcleo ao banco."""

    def stage_started(self, stage: str, prompt: str) -> None: ...
    def stage_completed(self, stage: str, output: Any) -> None: ...
    def stage_failed(self, stage: str, error: Exception) -> None: ...


def _coerce_output(value: Any, model_type: type[T]) -> T:
    if isinstance(value, model_type):
        return value
    if isinstance(value, str):
        return model_type.model_validate_json(value)  # type: ignore[attr-defined]
    return model_type.model_validate(value)  # type: ignore[attr-defined]


def _default_runner(agent: Any, prompt: str) -> Any:
    from agents import Runner

    return Runner.run_sync(agent, prompt)


def _execute_stage(
    *,
    stage: str,
    agent: Any,
    prompt: str,
    model_type: type[T],
    runner: RunnerFn,
    observer: TextCoreObserver | None,
) -> T:
    if observer is not None:
        observer.stage_started(stage, prompt)
    try:
        execution = runner(agent, prompt)
        output = _coerce_output(execution.final_output, model_type)
    except Exception as exc:
        if observer is not None:
            observer.stage_failed(stage, exc)
        raise
    if observer is not None:
        observer.stage_completed(stage, output)
    return output


def run_text_core(
    request: CampaignRequest,
    *,
    runner: RunnerFn | None = None,
    observer: TextCoreObserver | None = None,
) -> TextCoreResult:
    """Executa Researcher -> Strategist -> Copywriter.

    O runner pode ser injetado nos testes. Em produção, a execução usa
    OpenAI Agents SDK e exige OPENAI_API_KEY no ambiente. O observer é uma
    interface opcional de lifecycle usada pela persistência da Etapa 3.
    """

    if runner is None:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError(
                "OPENAI_API_KEY não está disponível no ambiente. "
                "Configure a chave fora do Git antes de executar o núcleo textual."
            )
        runner = _default_runner

    request_json = request.model_dump_json(indent=2)

    research = _execute_stage(
        stage="researcher",
        agent=build_researcher(),
        prompt="PEDIDO ORIGINAL:\n" + request_json,
        model_type=ResearchBrief,
        runner=runner,
        observer=observer,
    )

    strategy_prompt = (
        "PEDIDO ORIGINAL:\n"
        + request_json
        + "\n\nRESEARCH BRIEF:\n"
        + research.model_dump_json(indent=2)
    )
    strategy = _execute_stage(
        stage="strategist",
        agent=build_strategist(),
        prompt=strategy_prompt,
        model_type=StrategyBrief,
        runner=runner,
        observer=observer,
    )

    copy_prompt = (
        "PEDIDO ORIGINAL:\n"
        + request_json
        + "\n\nRESEARCH BRIEF:\n"
        + research.model_dump_json(indent=2)
        + "\n\nSTRATEGY BRIEF:\n"
        + strategy.model_dump_json(indent=2)
    )
    copy = _execute_stage(
        stage="copywriter",
        agent=build_copywriter(),
        prompt=copy_prompt,
        model_type=CopyPackage,
        runner=runner,
        observer=observer,
    )

    return TextCoreResult(
        request=request,
        research=research,
        strategy=strategy,
        copy=copy,
        publication_authorized=False,
    )


def result_as_json(result: TextCoreResult) -> str:
    return json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2)
