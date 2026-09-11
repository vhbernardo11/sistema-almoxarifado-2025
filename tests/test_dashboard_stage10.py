from datetime import datetime, timezone

from integra.dashboard import build_test_dashboard_snapshot


def test_stage10_dashboard_approval_queue_is_test_only():
    now = datetime(2026, 9, 11, 15, 0, tzinfo=timezone.utc)
    approvals = [
        {
            "id": "a-test", "run_id": "run-test", "decision": "pending", "content_digest": "abc",
            "metadata": {"stage": 10, "purpose": "text_review_test", "test_mode": True,
                         "test_actor_id": "stage8-test-user-001", "publication_authorized": False,
                         "preview": {"headline": "Campanha de teste", "short_caption": "Legenda de teste", "call_to_action": "Conheça"}},
        },
        {
            "id": "a-real", "run_id": "run-real", "decision": "pending", "content_digest": "xyz",
            "metadata": {"stage": 10, "test_mode": False, "test_actor_id": "real-user-001", "publication_authorized": True},
        },
    ]
    snapshot = build_test_dashboard_snapshot(jobs=[], ticks=[], alerts=[], actors=[], approvals=approvals, now=now)
    assert len(snapshot.approvals) == 1
    assert snapshot.approvals[0].id == "a-test"
    assert snapshot.approvals[0].decision == "pending"
    assert snapshot.approvals[0].publication_authorized is False
    assert snapshot.approvals[0].preview["headline"] == "Campanha de teste"
    assert snapshot.waiting_approval == 1
