from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

JobStatus = Literal["pending", "running", "retry", "completed", "failed", "cancelled"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RetryPolicy(BaseModel):
    base_seconds: int = Field(default=15, ge=1)
    multiplier: float = Field(default=2.0, ge=1.0)
    max_seconds: int = Field(default=900, ge=1)

    def delay_for_attempt(self, attempt: int) -> int:
        exponent = max(attempt - 1, 0)
        return min(int(self.base_seconds * (self.multiplier**exponent)), self.max_seconds)


class JobRecord(BaseModel):
    id: str
    job_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    status: JobStatus = "pending"
    run_id: str | None = None
    task_id: str | None = None
    priority: int = 100
    attempt: int = 0
    max_attempts: int = 3
    available_at: datetime = Field(default_factory=utc_now)
    locked_by: str | None = None
    locked_at: datetime | None = None
    heartbeat_at: datetime | None = None
    last_error: str | None = None
    result: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    finished_at: datetime | None = None


class ScheduleRecord(BaseModel):
    id: str
    name: str
    job_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    interval_seconds: int = Field(ge=60)
    next_run_at: datetime
    enabled: bool = True
    priority: int = 100
    max_attempts: int = 3


class ResumePlan(BaseModel):
    run_id: str
    can_resume: bool
    checkpoint_key: str | None = None
    resume_sequence: int | None = None
    snapshot: dict[str, Any] = Field(default_factory=dict)
    reason: str | None = None


class WorkerTickResult(BaseModel):
    worker_id: str
    schedules_materialized: int = 0
    stale_jobs_requeued: int = 0
    claimed_job_id: str | None = None
    job_status: JobStatus | None = None
    recovered_run_id: str | None = None
    detail: str | None = None
