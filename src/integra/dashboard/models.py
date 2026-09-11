from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

DashboardHealth = Literal["healthy", "degraded", "idle"]


class DashboardJob(BaseModel):
    id: str
    job_type: str
    status: str
    attempt: int = 0
    max_attempts: int = 0
    test_actor_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_error: str | None = None
    result: dict[str, Any] = Field(default_factory=dict)


class DashboardTick(BaseModel):
    worker_id: str
    status: str
    jobs_claimed: int = 0
    jobs_completed: int = 0
    jobs_retried: int = 0
    jobs_failed: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None


class DashboardAlert(BaseModel):
    severity: str
    kind: str
    message: str
    test_actor_id: str | None = None
    resolved: bool = False
    created_at: datetime | None = None


class DashboardSnapshot(BaseModel):
    test_mode: bool = True
    health: DashboardHealth = "idle"
    generated_at: datetime
    actors: list[str] = Field(default_factory=list)
    jobs_total: int = 0
    jobs_completed: int = 0
    jobs_retrying: int = 0
    jobs_failed: int = 0
    jobs_pending: int = 0
    waiting_approval: int = 0
    unresolved_alerts: int = 0
    last_worker_tick_at: datetime | None = None
    jobs: list[DashboardJob] = Field(default_factory=list)
    ticks: list[DashboardTick] = Field(default_factory=list)
    alerts: list[DashboardAlert] = Field(default_factory=list)
