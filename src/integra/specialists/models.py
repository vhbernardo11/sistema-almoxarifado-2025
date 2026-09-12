from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

SpecialistId = Literal[
    "researcher",
    "strategist",
    "copywriter",
    "reviewer",
    "programmer",
    "tester",
    "commercial",
    "legal_reviewer",
    "seo_analyst",
    "analytics",
]
# Compatibilidade com o nome histórico da Etapa 12.
Stage12SpecialistId = SpecialistId


class SpecialistExecutionError(RuntimeError):
    pass


class SpecialistTask(BaseModel):
    specialist_id: SpecialistId
    actor_id: str = Field(min_length=8)
    objective: str = Field(min_length=5)
    payload: dict[str, Any] = Field(default_factory=dict)
    test_mode: bool = True
    publication_authorized: bool = False
    external_actions_authorized: bool = False


class SpecialistResult(BaseModel):
    specialist_id: SpecialistId
    actor_id: str
    status: Literal["completed", "needs_review"]
    data: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    requires_human_review: bool = False
    publication_authorized: bool = False
    external_actions_authorized: bool = False
