from __future__ import annotations

from typing import Any, Callable

from integra.approval import ApprovalGate
from integra.approval.store import ApprovalStore
from integra.autonomy import CheckpointResumeCoordinator, ResumeJobHandler, RetryPolicy, Worker

from .guards import require_stage8_test_actor
from .handlers import build_stage8_handlers


def build_stage10_handlers(
    *,
    memory_store: Any,
    approval_store: ApprovalStore,
    text_runner: Any = None,
) -> dict[str, Any]:
    """Stage 10: núcleo textual real, mas somente para atores sintéticos.

    O handler text_core.run executa Researcher -> Strategist -> Copywriter e
    cria uma aprovação humana pendente para o payload exato. Publisher segue
    deliberadamente ausente.
    """
    handlers = build_stage8_handlers(memory_store=memory_store, text_runner=text_runner)
    base_text_handler = handlers["text_core.run"]
    gate = ApprovalGate(approval_store)

    def text_core_run(job: Any) -> dict[str, Any]:
        actor = require_stage8_test_actor(job.payload)
        base_result = base_text_handler(job)
        exact_payload = dict(base_result["result"])
        exact_payload["publication_authorized"] = False
        copy_payload = exact_payload.get("copy") or {}
        approval = gate.request_approval(
            run_id=base_result["run_id"],
            payload=exact_payload,
            metadata={
                "stage": 10,
                "purpose": "text_review_test",
                "test_mode": True,
                "test_actor_id": actor.id,
                "job_id": job.id,
                "publication_authorized": False,
                "preview": {
                    "headline": copy_payload.get("headline"),
                    "short_caption": copy_payload.get("short_caption"),
                    "call_to_action": copy_payload.get("call_to_action"),
                },
            },
        )
        return {
            **base_result,
            "result": exact_payload,
            "approval_id": approval.id,
            "content_digest": approval.content_digest,
            "waiting_approval": True,
            "publication_authorized": False,
            "test_actor_id": actor.id,
        }

    handlers["text_core.run"] = text_core_run
    handlers.pop("publisher.execute", None)
    return handlers


def build_stage10_worker(
    *,
    worker_id: str,
    queue_store: Any,
    memory_store: Any,
    approval_store: ApprovalStore,
    text_runner: Any = None,
    resume_executor: Callable[[Any], dict[str, Any] | None] | None = None,
    retry_policy: RetryPolicy | None = None,
) -> Worker:
    handlers = build_stage10_handlers(
        memory_store=memory_store,
        approval_store=approval_store,
        text_runner=text_runner,
    )
    recovery = None
    if resume_executor is not None:
        handlers["run.resume"] = ResumeJobHandler(
            memory_store=memory_store,
            executor=resume_executor,
        )
        recovery = CheckpointResumeCoordinator(
            memory_store=memory_store,
            queue_store=queue_store,
        )

    return Worker(
        worker_id=worker_id,
        store=queue_store,
        handlers=handlers,
        retry_policy=retry_policy or RetryPolicy(),
        recovery=recovery,
    )
