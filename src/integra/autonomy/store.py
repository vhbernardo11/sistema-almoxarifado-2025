from __future__ import annotations

import os
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol
from uuid import uuid4

from .models import JobRecord, ScheduleRecord


class QueueStoreError(RuntimeError):
    pass


class QueueStore(Protocol):
    def enqueue(
        self,
        *,
        job_type: str,
        payload: dict[str, Any],
        run_id: str | None = None,
        task_id: str | None = None,
        priority: int = 100,
        available_at: datetime | None = None,
        max_attempts: int = 3,
        idempotency_key: str | None = None,
    ) -> JobRecord: ...

    def claim_next(self, *, worker_id: str) -> JobRecord | None: ...
    def heartbeat(self, *, job_id: str, worker_id: str) -> None: ...
    def complete(self, *, job_id: str, result: dict[str, Any] | None = None) -> JobRecord: ...
    def fail(self, *, job_id: str, error: str, retry_delay_seconds: int | None) -> JobRecord: ...
    def requeue_stale(self, *, stale_after_seconds: int) -> int: ...
    def materialize_due_schedules(self, *, limit: int = 25) -> int: ...
    def create_schedule(
        self,
        *,
        name: str,
        job_type: str,
        payload: dict[str, Any],
        interval_seconds: int,
        next_run_at: datetime,
        priority: int = 100,
        max_attempts: int = 3,
    ) -> ScheduleRecord: ...


class SupabaseQueueStore:
    """Fila persistente usando as tabelas/rpcs `squad_*` da Etapa 7."""

    def __init__(self, client: Any):
        self.client = client

    @classmethod
    def from_env(cls) -> "SupabaseQueueStore":
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise QueueStoreError(
                "SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY são obrigatórios no backend."
            )
        try:
            from supabase import create_client
        except ImportError as exc:
            raise QueueStoreError("Instale o extra storage: pip install -e '.[storage]'") from exc
        return cls(create_client(url, key))

    @staticmethod
    def _data(response: Any) -> list[Any]:
        data = getattr(response, "data", None)
        if data is None and isinstance(response, dict):
            data = response.get("data")
        if data is None:
            return []
        if isinstance(data, list):
            return data
        return [data]

    @staticmethod
    def _record(row: dict[str, Any]) -> JobRecord:
        return JobRecord.model_validate(row)

    def enqueue(
        self,
        *,
        job_type: str,
        payload: dict[str, Any],
        run_id: str | None = None,
        task_id: str | None = None,
        priority: int = 100,
        available_at: datetime | None = None,
        max_attempts: int = 3,
        idempotency_key: str | None = None,
    ) -> JobRecord:
        row = {
            "job_type": job_type,
            "payload": payload,
            "run_id": run_id,
            "task_id": task_id,
            "priority": priority,
            "available_at": (available_at or datetime.now(timezone.utc)).isoformat(),
            "max_attempts": max_attempts,
            "idempotency_key": idempotency_key,
        }
        query = self.client.table("squad_jobs")
        if idempotency_key:
            response = query.upsert(row, on_conflict="idempotency_key", ignore_duplicates=True).execute()
            data = self._data(response)
            if not data:
                data = self._data(
                    self.client.table("squad_jobs")
                    .select("*")
                    .eq("idempotency_key", idempotency_key)
                    .limit(1)
                    .execute()
                )
        else:
            data = self._data(query.insert(row).execute())
        if not data:
            raise QueueStoreError("Supabase não retornou o job enfileirado.")
        return self._record(data[0])

    def claim_next(self, *, worker_id: str) -> JobRecord | None:
        data = self._data(
            self.client.rpc("squad_claim_next_job", {"p_worker_id": worker_id}).execute()
        )
        return self._record(data[0]) if data else None

    def heartbeat(self, *, job_id: str, worker_id: str) -> None:
        self.client.table("squad_jobs").update(
            {"heartbeat_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", job_id).eq("locked_by", worker_id).eq("status", "running").execute()

    def _get(self, job_id: str) -> JobRecord:
        data = self._data(
            self.client.table("squad_jobs").select("*").eq("id", job_id).limit(1).execute()
        )
        if not data:
            raise QueueStoreError(f"Job não encontrado: {job_id}")
        return self._record(data[0])

    def complete(self, *, job_id: str, result: dict[str, Any] | None = None) -> JobRecord:
        now = datetime.now(timezone.utc).isoformat()
        self.client.table("squad_jobs").update(
            {
                "status": "completed",
                "result": result or {},
                "finished_at": now,
                "locked_by": None,
                "locked_at": None,
                "heartbeat_at": None,
                "last_error": None,
            }
        ).eq("id", job_id).execute()
        return self._get(job_id)

    def fail(self, *, job_id: str, error: str, retry_delay_seconds: int | None) -> JobRecord:
        current = self._get(job_id)
        retry_allowed = retry_delay_seconds is not None and current.attempt < current.max_attempts
        payload: dict[str, Any] = {
            "status": "retry" if retry_allowed else "failed",
            "last_error": error,
            "locked_by": None,
            "locked_at": None,
            "heartbeat_at": None,
        }
        if retry_allowed:
            payload["available_at"] = (
                datetime.now(timezone.utc) + timedelta(seconds=retry_delay_seconds)
            ).isoformat()
        else:
            payload["finished_at"] = datetime.now(timezone.utc).isoformat()
        self.client.table("squad_jobs").update(payload).eq("id", job_id).execute()
        return self._get(job_id)

    def requeue_stale(self, *, stale_after_seconds: int) -> int:
        data = self._data(
            self.client.rpc(
                "squad_requeue_stale_jobs", {"p_stale_seconds": stale_after_seconds}
            ).execute()
        )
        if not data:
            return 0
        value = data[0]
        if isinstance(value, dict):
            return int(next(iter(value.values())))
        return int(value)

    def materialize_due_schedules(self, *, limit: int = 25) -> int:
        data = self._data(
            self.client.rpc("squad_materialize_due_schedules", {"p_limit": limit}).execute()
        )
        if not data:
            return 0
        value = data[0]
        if isinstance(value, dict):
            return int(next(iter(value.values())))
        return int(value)

    def create_schedule(
        self,
        *,
        name: str,
        job_type: str,
        payload: dict[str, Any],
        interval_seconds: int,
        next_run_at: datetime,
        priority: int = 100,
        max_attempts: int = 3,
    ) -> ScheduleRecord:
        data = self._data(
            self.client.table("squad_schedules").insert(
                {
                    "name": name,
                    "job_type": job_type,
                    "payload": payload,
                    "interval_seconds": interval_seconds,
                    "next_run_at": next_run_at.isoformat(),
                    "priority": priority,
                    "max_attempts": max_attempts,
                }
            ).execute()
        )
        if not data:
            raise QueueStoreError("Supabase não retornou o agendamento criado.")
        return ScheduleRecord.model_validate(data[0])


class InMemoryQueueStore:
    """Fila determinística para testes: sem rede, sleeps ou segredos."""

    def __init__(self, *, now_fn=None) -> None:
        self.jobs: dict[str, JobRecord] = {}
        self.schedules: dict[str, ScheduleRecord] = {}
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc))

    def enqueue(
        self,
        *,
        job_type: str,
        payload: dict[str, Any],
        run_id: str | None = None,
        task_id: str | None = None,
        priority: int = 100,
        available_at: datetime | None = None,
        max_attempts: int = 3,
        idempotency_key: str | None = None,
    ) -> JobRecord:
        if idempotency_key:
            for existing in self.jobs.values():
                if existing.idempotency_key == idempotency_key:
                    return existing.model_copy(deep=True)
        job = JobRecord(
            id=str(uuid4()),
            job_type=job_type,
            payload=deepcopy(payload),
            run_id=run_id,
            task_id=task_id,
            priority=priority,
            available_at=available_at or self.now_fn(),
            max_attempts=max_attempts,
            idempotency_key=idempotency_key,
            created_at=self.now_fn(),
        )
        self.jobs[job.id] = job
        return job.model_copy(deep=True)

    def claim_next(self, *, worker_id: str) -> JobRecord | None:
        now = self.now_fn()
        due = [
            job
            for job in self.jobs.values()
            if job.status in {"pending", "retry"} and job.available_at <= now
        ]
        if not due:
            return None
        due.sort(key=lambda j: (-j.priority, j.available_at, j.created_at or now))
        job = due[0]
        job.status = "running"
        job.attempt += 1
        job.locked_by = worker_id
        job.locked_at = now
        job.heartbeat_at = now
        job.updated_at = now
        return job.model_copy(deep=True)

    def heartbeat(self, *, job_id: str, worker_id: str) -> None:
        job = self.jobs[job_id]
        if job.status == "running" and job.locked_by == worker_id:
            job.heartbeat_at = self.now_fn()

    def complete(self, *, job_id: str, result: dict[str, Any] | None = None) -> JobRecord:
        job = self.jobs[job_id]
        job.status = "completed"
        job.result = deepcopy(result or {})
        job.finished_at = self.now_fn()
        job.locked_by = job.locked_at = job.heartbeat_at = None
        job.last_error = None
        return job.model_copy(deep=True)

    def fail(self, *, job_id: str, error: str, retry_delay_seconds: int | None) -> JobRecord:
        job = self.jobs[job_id]
        retry_allowed = retry_delay_seconds is not None and job.attempt < job.max_attempts
        job.last_error = error
        job.locked_by = job.locked_at = job.heartbeat_at = None
        if retry_allowed:
            job.status = "retry"
            job.available_at = self.now_fn() + timedelta(seconds=retry_delay_seconds)
        else:
            job.status = "failed"
            job.finished_at = self.now_fn()
        return job.model_copy(deep=True)

    def requeue_stale(self, *, stale_after_seconds: int) -> int:
        now = self.now_fn()
        count = 0
        for job in self.jobs.values():
            heartbeat = job.heartbeat_at or job.locked_at
            if job.status != "running" or heartbeat is None:
                continue
            if heartbeat > now - timedelta(seconds=stale_after_seconds):
                continue
            job.last_error = "worker heartbeat expirado; job recuperado automaticamente"
            job.locked_by = job.locked_at = job.heartbeat_at = None
            if job.attempt < job.max_attempts:
                job.status = "retry"
                job.available_at = now
            else:
                job.status = "failed"
                job.finished_at = now
            count += 1
        return count

    def materialize_due_schedules(self, *, limit: int = 25) -> int:
        now = self.now_fn()
        due = [s for s in self.schedules.values() if s.enabled and s.next_run_at <= now]
        due.sort(key=lambda s: s.next_run_at)
        count = 0
        for schedule in due[:limit]:
            slot = int(schedule.next_run_at.timestamp())
            before = len(self.jobs)
            self.enqueue(
                job_type=schedule.job_type,
                payload=deepcopy(schedule.payload),
                priority=schedule.priority,
                max_attempts=schedule.max_attempts,
                idempotency_key=f"schedule:{schedule.id}:{slot}",
            )
            if len(self.jobs) > before:
                count += 1
            schedule.next_run_at = now + timedelta(seconds=schedule.interval_seconds)
        return count

    def create_schedule(
        self,
        *,
        name: str,
        job_type: str,
        payload: dict[str, Any],
        interval_seconds: int,
        next_run_at: datetime,
        priority: int = 100,
        max_attempts: int = 3,
    ) -> ScheduleRecord:
        if interval_seconds < 60:
            raise QueueStoreError("interval_seconds deve ser >= 60")
        schedule = ScheduleRecord(
            id=str(uuid4()),
            name=name,
            job_type=job_type,
            payload=deepcopy(payload),
            interval_seconds=interval_seconds,
            next_run_at=next_run_at,
            priority=priority,
            max_attempts=max_attempts,
        )
        self.schedules[schedule.id] = schedule
        return schedule.model_copy(deep=True)
