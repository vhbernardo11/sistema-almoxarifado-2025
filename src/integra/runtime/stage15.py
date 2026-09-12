from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

from pydantic import BaseModel, Field

from integra.autonomy import JobRecord, PermanentJobError
from integra.maestro import WorkRequest, plan_work
from integra.specialists import SpecialistResult, SpecialistTask, execute_specialist


class Stage15WorkflowRequest(BaseModel):
    actor_id: str = Field(min_length=8)
    work: WorkRequest
    step_payloads: dict[str, dict[str, Any]] = Field(default_factory=dict)
    test_mode: bool = True
    publication_authorized: bool = False
    external_actions_authorized: bool = False


class Stage15StepResult(BaseModel):
    sequence: int
    specialist_id: str
    status: str
    result: dict[str, Any]


class Stage15DurableState(BaseModel):
    actor_id: str
    route: str
    status: Literal["running", "interrupted", "blocked", "completed", "needs_review"] = "running"
    next_sequence: int = 0
    steps: list[Stage15StepResult] = Field(default_factory=list)
    completed: dict[str, dict[str, Any]] = Field(default_factory=dict)
    blockers: list[str] = Field(default_factory=list)
    requires_human_review: bool = False
    publication_authorized: bool = False
    external_actions_authorized: bool = False


def _guard(request: Stage15WorkflowRequest) -> None:
    if request.test_mode is not True:
        raise PermanentJobError("Etapa 15 aceita somente test_mode=true.")
    if not request.actor_id.startswith("stage8-test-"):
        raise PermanentJobError("Etapa 15 aceita somente atores sintéticos stage8-test-*.")
    if request.publication_authorized or request.external_actions_authorized:
        raise PermanentJobError("Etapa 15 não aceita autorização de publicação ou efeito externo.")


def _get_path(value: Any, path: str) -> Any:
    current = value
    for part in path.split(".") if path else []:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise PermanentJobError(f"Referência de etapa inválida: {path}")
    return current


def _resolve_refs(value: Any, completed: dict[str, dict[str, Any]]) -> Any:
    if isinstance(value, list):
        return [_resolve_refs(item, completed) for item in value]
    if isinstance(value, dict):
        if set(value) == {"$step", "path"}:
            specialist_id = str(value["$step"])
            if specialist_id not in completed:
                raise PermanentJobError(f"Etapa referenciada ainda não foi concluída: {specialist_id}")
            return _get_path(completed[specialist_id], str(value["path"]))
        return {key: _resolve_refs(item, completed) for key, item in value.items()}
    return value


def initialize_stage15_state(request: Stage15WorkflowRequest) -> Stage15DurableState:
    _guard(request)
    plan = plan_work(request.work)
    return Stage15DurableState(actor_id=request.actor_id, route=plan.route)


def advance_stage15_workflow(
    request: Stage15WorkflowRequest,
    *,
    state: Stage15DurableState | None = None,
    max_steps: int | None = None,
    executor: Callable[[SpecialistTask], SpecialistResult] = execute_specialist,
) -> Stage15DurableState:
    """Executa a partir do último checkpoint concluído, sem repetir etapas anteriores.

    `max_steps` existe para homologação de interrupção/retomada. Em produção, o
    estado equivalente é persistido no Supabase após cada etapa.
    """
    _guard(request)
    plan = plan_work(request.work)
    current = state.model_copy(deep=True) if state is not None else initialize_stage15_state(request)

    if current.actor_id != request.actor_id or current.route != plan.route:
        raise PermanentJobError("Checkpoint da Etapa 15 não pertence a este ator/rota.")
    if current.publication_authorized or current.external_actions_authorized:
        raise PermanentJobError("Checkpoint tentou atravessar a barreira fail-closed.")
    if current.next_sequence < 0 or current.next_sequence > len(plan.steps):
        raise PermanentJobError("Checkpoint possui next_sequence inválido.")

    current.status = "running"
    current.blockers = []
    processed = 0

    for step in plan.steps[current.next_sequence :]:
        raw_payload = request.step_payloads.get(step.specialist_id)
        if raw_payload is None:
            current.status = "blocked"
            current.blockers.append(
                f"Payload ausente para {step.specialist_name} ({step.specialist_id})."
            )
            return current

        payload = _resolve_refs(raw_payload, current.completed)
        task = SpecialistTask(
            specialist_id=step.specialist_id,
            actor_id=request.actor_id,
            objective=step.objective,
            payload=payload,
            test_mode=True,
            publication_authorized=False,
            external_actions_authorized=False,
        )
        result = executor(task)
        dumped = result.model_dump(mode="json")
        if dumped.get("publication_authorized") is True or dumped.get("external_actions_authorized") is True:
            raise PermanentJobError("Especialista violou o contrato fail-closed da Etapa 15.")

        current.completed[step.specialist_id] = dumped
        current.steps.append(
            Stage15StepResult(
                sequence=step.sequence,
                specialist_id=step.specialist_id,
                status=result.status,
                result=dumped,
            )
        )
        current.next_sequence = step.sequence + 1
        current.requires_human_review = current.requires_human_review or result.requires_human_review
        processed += 1

        if max_steps is not None and processed >= max_steps and current.next_sequence < len(plan.steps):
            current.status = "interrupted"
            return current

    current.status = "needs_review" if current.requires_human_review else "completed"
    current.publication_authorized = False
    current.external_actions_authorized = False
    return current


def build_stage15_job_payload(request: Stage15WorkflowRequest) -> dict[str, Any]:
    _guard(request)
    return {
        "test_mode": True,
        "test_actor_id": request.actor_id,
        "work": request.work.model_dump(mode="json"),
        "step_payloads": request.step_payloads,
        "durable_workflow": True,
        "publication_authorized": False,
        "external_actions_authorized": False,
    }


def enqueue_stage15_workflow(
    store: Any,
    request: Stage15WorkflowRequest,
    *,
    priority: int = 100,
    max_attempts: int = 3,
    idempotency_key: str | None = None,
) -> JobRecord:
    return store.enqueue(
        job_type="maestro.workflow.v2",
        payload=build_stage15_job_payload(request),
        priority=priority,
        max_attempts=max_attempts,
        idempotency_key=idempotency_key,
    )


def execute_stage15_workflow_job(job: JobRecord) -> dict[str, Any]:
    if job.job_type != "maestro.workflow.v2":
        raise PermanentJobError(f"job_type não pertence à Etapa 15: {job.job_type}")
    payload = job.payload
    request = Stage15WorkflowRequest(
        actor_id=str(payload.get("test_actor_id", "")),
        work=WorkRequest.model_validate(payload.get("work", {})),
        step_payloads=payload.get("step_payloads", {}),
        test_mode=payload.get("test_mode") is True,
        publication_authorized=payload.get("publication_authorized") is True,
        external_actions_authorized=payload.get("external_actions_authorized") is True,
    )
    state = advance_stage15_workflow(request)
    return {
        "workflow": state.model_dump(mode="json"),
        "waiting_approval": state.requires_human_review,
        "publication_authorized": False,
        "external_actions_authorized": False,
        "test_actor_id": request.actor_id,
        "runtime": "stage15-python",
    }
