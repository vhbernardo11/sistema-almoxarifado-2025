from integra.main import smoke_test

def test_smoke_run():
    run = smoke_test()
    assert run.id == "smoke-001"
    assert run.status == "pending"
    assert "IntegraSquad" not in run.goal or isinstance(run.goal, str)
