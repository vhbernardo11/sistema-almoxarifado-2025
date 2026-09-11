from datetime import datetime, timedelta, timezone

from integra.dashboard import build_test_dashboard_snapshot


def test_dashboard_filters_real_users():
    now = datetime(2026, 9, 11, 10, 0, tzinfo=timezone.utc)
    jobs = [
        {"id": "t1", "job_type": "test.echo", "status": "completed", "attempt": 1, "max_attempts": 3,
         "payload": {"test_mode": True, "test_actor_id": "stage8-test-user-001"}, "result": {}},
        {"id": "r1", "job_type": "text_core.run", "status": "completed", "attempt": 1, "max_attempts": 3,
         "payload": {"test_mode": False, "test_actor_id": "real-user-999"}, "result": {}},
    ]
    snapshot = build_test_dashboard_snapshot(jobs=jobs, ticks=[], alerts=[], actors=[], now=now)
    assert snapshot.jobs_total == 1
    assert snapshot.jobs[0].id == "t1"


def test_waiting_approval_is_visible_but_not_authorized():
    now = datetime(2026, 9, 11, 10, 0, tzinfo=timezone.utc)
    jobs = [{
        "id": "a1", "job_type": "test.waiting_approval", "status": "completed", "attempt": 1, "max_attempts": 3,
        "payload": {"test_mode": True, "test_actor_id": "stage8-test-admin-001"},
        "result": {"waiting_approval": True, "publication_authorized": False},
    }]
    snapshot = build_test_dashboard_snapshot(jobs=jobs, ticks=[], alerts=[], actors=[], now=now)
    assert snapshot.waiting_approval == 1
    assert snapshot.jobs[0].result["publication_authorized"] is False


def test_recent_test_tick_marks_runtime_healthy():
    now = datetime(2026, 9, 11, 10, 0, tzinfo=timezone.utc)
    ticks = [{
        "worker_id": "stage8-edge-1", "status": "completed", "jobs_claimed": 1, "jobs_completed": 1,
        "jobs_retried": 0, "jobs_failed": 0, "started_at": now - timedelta(minutes=2),
        "finished_at": now - timedelta(minutes=1), "detail": {"test_only": True},
    }]
    snapshot = build_test_dashboard_snapshot(jobs=[], ticks=ticks, alerts=[], actors=[], now=now)
    assert snapshot.health == "healthy"


def test_old_tick_marks_runtime_degraded():
    now = datetime(2026, 9, 11, 10, 0, tzinfo=timezone.utc)
    ticks = [{
        "worker_id": "stage8-edge-1", "status": "completed", "jobs_claimed": 0, "jobs_completed": 0,
        "jobs_retried": 0, "jobs_failed": 0, "started_at": now - timedelta(minutes=20),
        "finished_at": now - timedelta(minutes=19), "detail": {"test_only": True},
    }]
    snapshot = build_test_dashboard_snapshot(jobs=[], ticks=ticks, alerts=[], actors=[], now=now)
    assert snapshot.health == "degraded"


def test_alerts_and_actors_are_test_only():
    now = datetime(2026, 9, 11, 10, 0, tzinfo=timezone.utc)
    alerts = [
        {"severity": "info", "kind": "waiting_approval", "message": "teste", "test_actor_id": "stage8-test-admin-001", "resolved": False},
        {"severity": "error", "kind": "real", "message": "real", "test_actor_id": "real-user", "resolved": False},
    ]
    actors = [
        {"id": "stage8-test-user-001", "enabled": True},
        {"id": "stage8-test-disabled", "enabled": False},
        {"id": "real-user", "enabled": True},
    ]
    snapshot = build_test_dashboard_snapshot(jobs=[], ticks=[], alerts=alerts, actors=actors, now=now)
    assert snapshot.unresolved_alerts == 1
    assert snapshot.actors == ["stage8-test-user-001"]
