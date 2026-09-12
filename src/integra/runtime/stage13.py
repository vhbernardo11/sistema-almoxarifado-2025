from __future__ import annotations

from typing import Any

from integra.autonomy import JobRecord, PermanentJobError
from integra.specialists import SpecialistTask, execute_specialist

SPECIALIST_JOB_TYPES = {
    "programmer": "specialist.programmer",
    "tester": "specialist.tester",
    "commercial": "specialist.commercial",
    "legal_reviewer": "specialist.legal_reviewer",
    "seo_analyst": "specialist.seo_analyst",
    "analytics": "specialist.analytics",
}
JOB_TYPE_TO_SPECIALIST = {value: key for key, value in SPECIALIST_JOB_TYPES.items()}


def _assert_test_boundary(task: SpecialistTask) -> None:
    if task.test_mode is not True:
        raise PermanentJobError("Etapa 13 aceita somente test_mode=true.")
    if not task.actor_id.startswith("stage8-test-"):
        raise PermanentJobError("Etapa 13 aceita somente atores sintéticos stage8-test-*.")
    if task.publication_authorized or task.external_actions_authorized:
        raise PermanentJobError("Etapa 13 não aceita autorização de publicação ou efeito externo.")


def build_specialist_job_payload(task: SpecialistTask) -> dict[str, Any]:
    _assert_test_boundary(task)
    return {
        "test_mode": True,
        "test_actor_id": task.actor_id,
        "objective": task.objective,
        "specialist_payload": task.payload,
        "publication_authorized": False,
        "external_actions_authorized": False,
    }


def enqueue_specialist_task(
    store: Any,
    task: SpecialistTask,
    *,
    priority: int = 100,
    max_attempts: int = 3,
    idempotency_key: str | None = None,
) -> JobRecord:
    _assert_test_boundary(task)
    job_type = SPECIALIST_JOB_TYPES[task.specialist_id]
    return store.enqueue(
        job_type=job_type,
        payload=build_specialist_job_payload(task),
        priority=priority,
        max_attempts=max_attempts,
        idempotency_key=idempotency_key,
    )


def execute_specialist_job(job: JobRecord) -> dict[str, Any]:
    specialist_id = JOB_TYPE_TO_SPECIALIST.get(job.job_type)
    if specialist_id is None:
        raise PermanentJobError(f"job_type não pertence à Etapa 13: {job.job_type}")
    payload = job.payload
    task = SpecialistTask(
        specialist_id=specialist_id,
        actor_id=str(payload.get("test_actor_id", "")),
        objective=str(payload.get("objective", "")),
        payload=payload.get("specialist_payload", {}),
        test_mode=payload.get("test_mode") is True,
        publication_authorized=payload.get("publication_authorized") is True,
        external_actions_authorized=payload.get("external_actions_authorized") is True,
    )
    _assert_test_boundary(task)
    result = execute_specialist(task)
    return {
        "specialist_id": result.specialist_id,
        "specialist_status": result.status,
        "specialist_result": result.model_dump(mode="json"),
        "requires_human_review": result.requires_human_review,
        "waiting_approval": result.requires_human_review,
        "publication_authorized": False,
        "external_actions_authorized": False,
        "test_actor_id": task.actor_id,
        "runtime": "stage13-python",
    }
