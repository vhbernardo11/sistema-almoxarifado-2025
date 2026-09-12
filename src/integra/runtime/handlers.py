from __future__ import annotations

from pathlib import Path
from typing import Any

from integra.autonomy import JobRecord, PermanentJobError
from integra.media.models import MediaManifest
from integra.media.reviewer import review_media
from integra.text_core.models import CampaignRequest
from integra.text_core.persistent import run_text_core_persistent

from .guards import require_stage8_test_actor
from .stage13 import JOB_TYPE_TO_SPECIALIST, execute_specialist_job
from .stage14 import execute_stage14_workflow_job


def _required(payload: dict[str, Any], key: str) -> Any:
    if key not in payload:
        raise PermanentJobError(f"campo obrigatório ausente: {key}")
    return payload[key]


def build_stage8_handlers(*, memory_store: Any, text_runner: Any = None) -> dict[str, Any]:
    """Handlers do runtime Python test-only. Publisher não é registrado."""

    def test_echo(job: JobRecord) -> dict[str, Any]:
        actor = require_stage8_test_actor(job.payload)
        return {"echoed": job.payload.get("message"), "test_actor_id": actor.id}

    def waiting_approval(job: JobRecord) -> dict[str, Any]:
        actor = require_stage8_test_actor(job.payload)
        return {"waiting_approval": True, "publication_authorized": False, "test_actor_id": actor.id}

    def text_core_run(job: JobRecord) -> dict[str, Any]:
        actor = require_stage8_test_actor(job.payload)
        request = CampaignRequest.model_validate(_required(job.payload, "request"))
        result = run_text_core_persistent(request, store=memory_store, runner=text_runner)
        return {
            "run_id": result.run_id,
            "result": result.result.model_dump(mode="json"),
            "resume_state": result.resume_state.model_dump(mode="json"),
            "publication_authorized": False,
            "test_actor_id": actor.id,
        }

    def media_review(job: JobRecord) -> dict[str, Any]:
        actor = require_stage8_test_actor(job.payload)
        manifest = MediaManifest.model_validate(_required(job.payload, "manifest"))
        video_path = Path(str(_required(job.payload, "video_path")))
        report = review_media(manifest, video_path)
        return {"review": report.model_dump(mode="json"), "test_actor_id": actor.id, "publication_authorized": False}

    handlers: dict[str, Any] = {
        "test.echo": test_echo,
        "test.waiting_approval": waiting_approval,
        "text_core.run": text_core_run,
        "media.review": media_review,
        "maestro.workflow": execute_stage14_workflow_job,
    }
    for job_type in JOB_TYPE_TO_SPECIALIST:
        handlers[job_type] = execute_specialist_job
    return handlers
