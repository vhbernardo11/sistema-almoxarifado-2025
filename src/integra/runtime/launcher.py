from __future__ import annotations

from typing import Any, Callable

from integra.autonomy import (
    CheckpointResumeCoordinator,
    ResumeJobHandler,
    RetryPolicy,
    Worker,
)

from .handlers import build_stage8_handlers


def build_stage8_worker(
    *,
    worker_id: str,
    queue_store: Any,
    memory_store: Any,
    text_runner: Any = None,
    resume_executor: Callable[[Any], dict[str, Any] | None] | None = None,
    retry_policy: RetryPolicy | None = None,
) -> Worker:
    handlers = build_stage8_handlers(memory_store=memory_store, text_runner=text_runner)
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
