from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .models import JobRecord, RetryPolicy, WorkerTickResult
from .resume import CheckpointResumeCoordinator
from .store import QueueStore

JobHandler = Callable[[JobRecord], dict[str, Any] | None]


class PermanentJobError(RuntimeError):
    """Erro que não deve consumir novas tentativas."""


class Worker:
    """Executa uma unidade de trabalho por tick, sem loop infinito oculto."""

    def __init__(
        self,
        *,
        worker_id: str,
        store: QueueStore,
        handlers: dict[str, JobHandler],
        retry_policy: RetryPolicy | None = None,
        stale_after_seconds: int = 300,
        recovery: CheckpointResumeCoordinator | None = None,
    ) -> None:
        self.worker_id = worker_id
        self.store = store
        self.handlers = handlers
        self.retry_policy = retry_policy or RetryPolicy()
        self.stale_after_seconds = stale_after_seconds
        self.recovery = recovery

    def tick(self) -> WorkerTickResult:
        materialized = self.store.materialize_due_schedules()
        stale = self.store.requeue_stale(stale_after_seconds=self.stale_after_seconds)
        job = self.store.claim_next(worker_id=self.worker_id)
        if job is None:
            return WorkerTickResult(
                worker_id=self.worker_id,
                schedules_materialized=materialized,
                stale_jobs_requeued=stale,
                detail="queue_empty",
            )

        result = WorkerTickResult(
            worker_id=self.worker_id,
            schedules_materialized=materialized,
            stale_jobs_requeued=stale,
            claimed_job_id=job.id,
        )
        handler = self.handlers.get(job.job_type)
        if handler is None:
            failed = self.store.fail(
                job_id=job.id,
                error=f"handler ausente para job_type={job.job_type}",
                retry_delay_seconds=None,
            )
            result.job_status = failed.status
            result.detail = failed.last_error
            return result

        try:
            payload = handler(job) or {}
            completed = self.store.complete(job_id=job.id, result=payload)
            result.job_status = completed.status
            result.detail = "completed"
            return result
        except PermanentJobError as exc:
            failed = self.store.fail(
                job_id=job.id, error=str(exc), retry_delay_seconds=None
            )
        except Exception as exc:
            delay = self.retry_policy.delay_for_attempt(job.attempt)
            failed = self.store.fail(
                job_id=job.id, error=str(exc), retry_delay_seconds=delay
            )

        result.job_status = failed.status
        result.detail = failed.last_error
        if (
            failed.status == "failed"
            and failed.run_id
            and failed.job_type != "run.resume"
            and self.recovery is not None
        ):
            recovery_job = self.recovery.enqueue(failed.run_id)
            if recovery_job is not None:
                result.recovered_run_id = failed.run_id
        return result

    def run_until_idle(self, *, max_jobs: int = 100) -> list[WorkerTickResult]:
        """Drena jobs disponíveis agora, com limite explícito de segurança."""
        results: list[WorkerTickResult] = []
        for _ in range(max_jobs):
            item = self.tick()
            results.append(item)
            if item.claimed_job_id is None:
                break
        return results
