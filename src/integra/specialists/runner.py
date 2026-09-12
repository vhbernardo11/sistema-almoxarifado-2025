from __future__ import annotations

from .executors import EXECUTORS as STAGE12_EXECUTORS
from .models import SpecialistExecutionError, SpecialistResult, SpecialistTask
from .stage14_executors import STAGE14_EXECUTORS

EXECUTORS = {**STAGE12_EXECUTORS, **STAGE14_EXECUTORS}


def _guard_test_only(task: SpecialistTask) -> None:
    if task.test_mode is not True:
        raise SpecialistExecutionError("Especialistas determinísticos operam somente em test_mode=true.")
    if not task.actor_id.startswith("stage8-test-"):
        raise SpecialistExecutionError("Somente atores sintéticos stage8-test-* são aceitos.")
    if task.publication_authorized:
        raise SpecialistExecutionError("Especialistas nunca recebem autorização de publicação.")
    if task.external_actions_authorized:
        raise SpecialistExecutionError("Especialistas determinísticos não executam efeitos externos.")


def execute_specialist(task: SpecialistTask) -> SpecialistResult:
    _guard_test_only(task)
    executor = EXECUTORS.get(task.specialist_id)
    if executor is None:
        raise SpecialistExecutionError(f"Executor não registrado: {task.specialist_id}")
    result = executor(task)
    if result.publication_authorized or result.external_actions_authorized:
        raise SpecialistExecutionError("Executor violou o contrato fail-closed.")
    return result
