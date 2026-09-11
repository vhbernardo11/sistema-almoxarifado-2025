from __future__ import annotations

from typing import Any, Callable

from integra.memory.models import ResumeState
from integra.memory.store import MemoryStore

from .models import JobRecord, ResumePlan
from .store import QueueStore

ResumeExecutor = Callable[[ResumeState], dict[str, Any] | None]


class CheckpointResumeCoordinator:
    """Transforma um checkpoint persistido em um job idempotente de recuperação."""

    def __init__(self, *, memory_store: MemoryStore, queue_store: QueueStore):
        self.memory_store = memory_store
        self.queue_store = queue_store

    def plan(self, run_id: str) -> ResumePlan:
        state = self.memory_store.get_resume_state(run_id)
        if state.run_status in {"completed", "cancelled"}:
            return ResumePlan(run_id=run_id, can_resume=False, reason=f"run {state.run_status}")
        if not state.checkpoint_key:
            return ResumePlan(run_id=run_id, can_resume=False, reason="checkpoint ausente")
        if state.resume_sequence is None:
            return ResumePlan(
                run_id=run_id,
                can_resume=False,
                checkpoint_key=state.checkpoint_key,
                snapshot=state.snapshot,
                reason="checkpoint não possui próxima sequência",
            )
        return ResumePlan(
            run_id=run_id,
            can_resume=True,
            checkpoint_key=state.checkpoint_key,
            resume_sequence=state.resume_sequence,
            snapshot=state.snapshot,
        )

    def enqueue(self, run_id: str) -> JobRecord | None:
        plan = self.plan(run_id)
        if not plan.can_resume:
            return None
        return self.queue_store.enqueue(
            job_type="run.resume",
            run_id=run_id,
            payload=plan.model_dump(mode="json"),
            priority=1000,
            max_attempts=2,
            idempotency_key=(
                f"resume:{run_id}:{plan.checkpoint_key}:{plan.resume_sequence}"
            ),
        )


class ResumeJobHandler:
    """Executa a continuação usando um executor específico do pipeline.

    O Worker não conhece OpenAI, vídeo ou Publisher. Ele apenas fornece o
    envelope de recuperação; o executor do pipeline decide como continuar.
    """

    def __init__(self, *, memory_store: MemoryStore, executor: ResumeExecutor):
        self.memory_store = memory_store
        self.executor = executor

    def __call__(self, job: JobRecord) -> dict[str, Any]:
        if not job.run_id:
            raise RuntimeError("run.resume exige run_id")
        state = self.memory_store.get_resume_state(job.run_id)
        result = self.executor(state) or {}
        return {"run_id": job.run_id, "checkpoint": state.checkpoint_key, **result}
