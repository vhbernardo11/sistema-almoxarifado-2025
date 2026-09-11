from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from .models import DashboardAlert, DashboardApproval, DashboardJob, DashboardSnapshot, DashboardTick

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
    approvals: Iterable[dict[str, Any]] = (),
    now: datetime | None = None,
) -> DashboardSnapshot:
    """Build a read-only Stage 9/10 snapshot using synthetic actors only."""
    current = now or datetime.now(timezone.utc)

    safe_jobs: list[DashboardJob] = []
    for row in jobs:
        payload = _as_dict(row.get("payload"))
        actor = payload.get("test_actor_id")
        if payload.get("test_mode") is not True or not _is_test_actor(actor):
            continue
        safe_jobs.append(DashboardJob(
            id=str(row.get("id", "")), job_type=str(row.get("job_type", "unknown")),
            status=str(row.get("status", "unknown")), attempt=int(row.get("attempt") or 0),
            max_attempts=int(row.get("max_attempts") or 0), test_actor_id=actor,
            created_at=row.get("created_at"), updated_at=row.get("updated_at"),
            last_error=row.get("last_error"), result=_as_dict(row.get("result")),
        ))

    safe_approvals: list[DashboardApproval] = []
    for row in approvals:
        metadata = _as_dict(row.get("metadata"))
        actor = metadata.get("test_actor_id")
        if metadata.get("test_mode") is not True or not _is_test_actor(actor):
            continue
        safe_approvals.append(DashboardApproval(
            id=str(row.get("id", "")), run_id=str(row.get("run_id", "")),
            decision=str(row.get("decision", "pending")), content_digest=str(row.get("content_digest", "")),
            test_actor_id=str(actor), purpose=metadata.get("purpose"), preview=_as_dict(metadata.get("preview")),
            publication_authorized=metadata.get("publication_authorized") is True,
            created_at=row.get("created_at"), decided_at=row.get("decided_at"),
        ))

    safe_ticks = [DashboardTick.model_validate(row) for row in ticks if _as_dict(row.get("detail")).get("test_only") is True]
    safe_alerts = [DashboardAlert.model_validate(row) for row in alerts if _is_test_actor(row.get("test_actor_id"))]
    safe_actors = sorted(str(row.get("id")) for row in actors if row.get("enabled") is True and _is_test_actor(row.get("id")))

    last_tick = max((tick.finished_at or tick.started_at for tick in safe_ticks if tick.finished_at or tick.started_at), default=None)
    if last_tick is None:
        health = "idle"
    elif current - last_tick <= timedelta(minutes=12) and not any(tick.status == "failed" for tick in safe_ticks[:1]):
        health = "healthy"
    else:
        health = "degraded"

    waiting_from_jobs = sum(j.result.get("waiting_approval") is True for j in safe_jobs)
    pending_approvals = sum(a.decision == "pending" for a in safe_approvals)

    return DashboardSnapshot(
        health=health, generated_at=current, actors=safe_actors,
        jobs_total=len(safe_jobs), jobs_completed=sum(j.status == "completed" for j in safe_jobs),
        jobs_retrying=sum(j.status == "retry" for j in safe_jobs), jobs_failed=sum(j.status == "failed" for j in safe_jobs),
        jobs_pending=sum(j.status in {"pending", "running"} for j in safe_jobs),
        waiting_approval=max(waiting_from_jobs, pending_approvals),
        unresolved_alerts=sum(not alert.resolved for alert in safe_alerts), last_worker_tick_at=last_tick,
        jobs=safe_jobs, approvals=safe_approvals, ticks=safe_ticks, alerts=safe_alerts,
    )
