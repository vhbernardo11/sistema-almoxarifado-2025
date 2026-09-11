from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from .models import DashboardAlert, DashboardJob, DashboardSnapshot, DashboardTick

TEST_ACTOR_PREFIX = "stage8-test-"


def _is_test_actor(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(TEST_ACTOR_PREFIX)


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def build_test_dashboard_snapshot(
    *,
    jobs: Iterable[dict[str, Any]],
    ticks: Iterable[dict[str, Any]],
    alerts: Iterable[dict[str, Any]],
    actors: Iterable[dict[str, Any]],
    now: datetime | None = None,
) -> DashboardSnapshot:
    """Build a read-only Stage 9 snapshot using synthetic actors only.

    Real jobs are excluded even when mixed into the input. A job is eligible only
    when payload.test_mode is true and payload.test_actor_id starts with the
    Stage 8 synthetic actor prefix.
    """
    current = now or datetime.now(timezone.utc)

    safe_jobs: list[DashboardJob] = []
    for row in jobs:
        payload = _as_dict(row.get("payload"))
        actor = payload.get("test_actor_id")
        if payload.get("test_mode") is not True or not _is_test_actor(actor):
            continue
        safe_jobs.append(
            DashboardJob(
                id=str(row.get("id", "")),
                job_type=str(row.get("job_type", "unknown")),
                status=str(row.get("status", "unknown")),
                attempt=int(row.get("attempt") or 0),
                max_attempts=int(row.get("max_attempts") or 0),
                test_actor_id=actor,
                created_at=row.get("created_at"),
                updated_at=row.get("updated_at"),
                last_error=row.get("last_error"),
                result=_as_dict(row.get("result")),
            )
        )

    safe_ticks = [
        DashboardTick.model_validate(row)
        for row in ticks
        if _as_dict(row.get("detail")).get("test_only") is True
    ]
    safe_alerts = [
        DashboardAlert.model_validate(row)
        for row in alerts
        if _is_test_actor(row.get("test_actor_id"))
    ]
    safe_actors = sorted(
        str(row.get("id"))
        for row in actors
        if row.get("enabled") is True and _is_test_actor(row.get("id"))
    )

    last_tick = max(
        (tick.finished_at or tick.started_at for tick in safe_ticks if tick.finished_at or tick.started_at),
        default=None,
    )
    if last_tick is None:
        health = "idle"
    elif current - last_tick <= timedelta(minutes=12) and not any(
        tick.status == "failed" for tick in safe_ticks[:1]
    ):
        health = "healthy"
    else:
        health = "degraded"

    return DashboardSnapshot(
        health=health,
        generated_at=current,
        actors=safe_actors,
        jobs_total=len(safe_jobs),
        jobs_completed=sum(j.status == "completed" for j in safe_jobs),
        jobs_retrying=sum(j.status == "retry" for j in safe_jobs),
        jobs_failed=sum(j.status == "failed" for j in safe_jobs),
        jobs_pending=sum(j.status in {"pending", "running"} for j in safe_jobs),
        waiting_approval=sum(j.result.get("waiting_approval") is True for j in safe_jobs),
        unresolved_alerts=sum(not alert.resolved for alert in safe_alerts),
        last_worker_tick_at=last_tick,
        jobs=safe_jobs,
        ticks=safe_ticks,
        alerts=safe_alerts,
    )
