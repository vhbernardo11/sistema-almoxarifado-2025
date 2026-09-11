from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class TestModeViolation(RuntimeError):
    pass


@dataclass(frozen=True)
class TestActor:
    id: str


def require_stage8_test_actor(payload: dict[str, Any]) -> TestActor:
    if payload.get("test_mode") is not True:
        raise TestModeViolation("Etapa 8 aceita somente payload com test_mode=true.")
    actor_id = str(payload.get("test_actor_id") or "")
    if not actor_id.startswith("stage8-test-"):
        raise TestModeViolation("Etapa 8 aceita somente usuários de teste stage8-test-*.")
    return TestActor(id=actor_id)
