from datetime import timezone

from integra.main import smoke_test


def test_smoke_run_is_valid():
    run = smoke_test()
    assert run.id == "smoke-001"
    assert run.status == "pending"
    assert run.goal
    assert run.created_at.tzinfo == timezone.utc
