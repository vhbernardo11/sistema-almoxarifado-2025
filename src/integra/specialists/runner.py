from __future__ import annotations

from .executors import EXECUTORS
from .models import SpecialistExecutionError, SpecialistResult, SpecialistTask


def _guard_test_only(task: SpecialistTask) -> None:
    if task.test_mode is not True:
        raise SpecialistExecutionError("Etapa 12 opera somente em test_mode=true.")
    if not task.actor_id.startswith("stage8-test-"):
        raise SpecialistExecutionError("Etapa 12 aceita somente atores sintéticos stage8-test-*.")
    if task.publication_authorized:
        raise SpecialistExecutionError("Especialistas da Etapa 12 nunca recebem autorização de publicação.")
    if task.external_actions_authorized:
        raise SpecialistExecutionError("Especialistas da Etapa 12 não executam efeitos externos.")


def execute_specialist(task: SpecialistTask) -> SpecialistResult:
    _guard_test_only(task)
    executor = EXECUTORS.get(task.specialist_id)
    if executor is None:
        raise SpecialistExecutionError(f"Executor não registrado: {task.specialist_id}")
    result = executor(task)
    if result.publication_authorized or result.external_actions_authorized:
        raise SpecialistExecutionError("Executor violou o contrato fail-closed da Etapa 12.")
    return result
