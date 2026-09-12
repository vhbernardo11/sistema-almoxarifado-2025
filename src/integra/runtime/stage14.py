from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from integra.autonomy import JobRecord, PermanentJobError
from integra.maestro import WorkRequest, plan_work
from integra.specialists import SpecialistTask, execute_specialist


class Stage14WorkflowRequest(BaseModel):
    actor_id: str = Field(min_length=8)
    work: WorkRequest
    step_payloads: dict[str, dict[str, Any]] = Field(default_factory=dict)
    test_mode: bool = True
    publication_authorized: bool = False
    external_actions_authorized: bool = False


class Stage14StepResult(BaseModel):
    sequence: int
    specialist_id: str
    status: str
    result: dict[str, Any]


class Stage14WorkflowResult(BaseModel):
    actor_id: str
    route: str
    status: str
    steps: list[Stage14StepResult]
    blockers: list[str] = Field(default_factory=list)
    requires_human_review: bool = False
    publication_authorized: bool = False
    external_actions_authorized: bool = False


def _guard(request: Stage14WorkflowRequest) -> None:
    if request.test_mode is not True:
        raise PermanentJobError("Etapa 14 aceita somente test_mode=true.")
    if not request.actor_id.startswith("stage8-test-"):
        raise PermanentJobError("Etapa 14 aceita somente atores sintéticos stage8-test-*.")
    if request.publication_authorized or request.external_actions_authorized:
        raise PermanentJobError("Etapa 14 não aceita autorização de publicação ou efeito externo.")


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
                raise PermanentJobError(f"Etapa referenciada ainda não existe: {specialist_id}")
            return _get_path(completed[specialist_id], str(value["path"]))
        return {key: _resolve_refs(item, completed) for key, item in value.items()}
    return value


def run_stage14_workflow(request: Stage14WorkflowRequest) -> Stage14WorkflowResult:
    _guard(request)
    plan = plan_work(request.work)
    steps: list[Stage14StepResult] = []
    completed: dict[str, dict[str, Any]] = {}
    blockers: list[str] = []
    needs_review = False

    for step in plan.steps:
        raw_payload = request.step_payloads.get(step.specialist_id)
        if raw_payload is None:
            blockers.append(f"Payload ausente para {step.specialist_name} ({step.specialist_id}).")
            break
        payload = _resolve_refs(raw_payload, completed)
        task = SpecialistTask(
            specialist_id=step.specialist_id,
            actor_id=request.actor_id,
            objective=step.objective,
            payload=payload,
            test_mode=True,
            publication_authorized=False,
            external_actions_authorized=False,
        )
        result = execute_specialist(task)
        dumped = result.model_dump(mode="json")
        completed[step.specialist_id] = dumped
        steps.append(
            Stage14StepResult(
                sequence=step.sequence,
                specialist_id=step.specialist_id,
                status=result.status,
                result=dumped,
            )
        )
        needs_review = needs_review or result.requires_human_review

    status = "blocked" if blockers else ("needs_review" if needs_review else "completed")
    return Stage14WorkflowResult(
        actor_id=request.actor_id,
        route=plan.route,
        status=status,
        steps=steps,
        blockers=blockers,
        requires_human_review=needs_review,
        publication_authorized=False,
        external_actions_authorized=False,
    )


def build_stage14_job_payload(request: Stage14WorkflowRequest) -> dict[str, Any]:
    _guard(request)
    return {
        "test_mode": True,
        "test_actor_id": request.actor_id,
        "work": request.work.model_dump(mode="json"),
        "step_payloads": request.step_payloads,
        "publication_authorized": False,
        "external_actions_authorized": False,
    }


def enqueue_stage14_workflow(
    store: Any,
    request: Stage14WorkflowRequest,
    *,
    priority: int = 100,
    max_attempts: int = 3,
    idempotency_key: str | None = None,
) -> JobRecord:
    return store.enqueue(
        job_type="maestro.workflow",
        payload=build_stage14_job_payload(request),
        priority=priority,
        max_attempts=max_attempts,
        idempotency_key=idempotency_key,
    )


def execute_stage14_workflow_job(job: JobRecord) -> dict[str, Any]:
    if job.job_type != "maestro.workflow":
        raise PermanentJobError(f"job_type não pertence à Etapa 14: {job.job_type}")
    payload = job.payload
    request = Stage14WorkflowRequest(
        actor_id=str(payload.get("test_actor_id", "")),
        work=WorkRequest.model_validate(payload.get("work", {})),
        step_payloads=payload.get("step_payloads", {}),
        test_mode=payload.get("test_mode") is True,
        publication_authorized=payload.get("publication_authorized") is True,
        external_actions_authorized=payload.get("external_actions_authorized") is True,
    )
    result = run_stage14_workflow(request)
    return {
        "workflow": result.model_dump(mode="json"),
        "waiting_approval": result.requires_human_review,
        "publication_authorized": False,
        "external_actions_authorized": False,
        "test_actor_id": request.actor_id,
        "runtime": "stage14-python",
    }
