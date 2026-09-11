from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

WorkKind = Literal[
    "auto",
    "campaign",
    "software",
    "commercial",
    "legal",
    "seo",
    "analytics",
    "operations",
]
CapabilityState = Literal["implemented", "prepared", "blocked"]
ExternalEffect = Literal["none", "read", "write", "publish"]


class WorkRequest(BaseModel):
    objective: str = Field(min_length=8)
    kind: WorkKind = "auto"
    context: dict[str, Any] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    allow_external_actions: bool = False


class SpecialistSpec(BaseModel):
    id: str
    name: str
    purpose: str
    state: CapabilityState
    external_effect: ExternalEffect = "none"
    approval_required: bool = False
    notes: str | None = None


class PlanStep(BaseModel):
    sequence: int = Field(ge=0)
    specialist_id: str
    specialist_name: str
    objective: str
    state: CapabilityState
    executable: bool
    external_effect: ExternalEffect = "none"
    depends_on: list[int] = Field(default_factory=list)


class MaestroPlan(BaseModel):
    request: WorkRequest
    route: ExcludeAutoWorkKind
    steps: list[PlanStep]
    ready_for_execution: bool
    blockers: list[str] = Field(default_factory=list)
    publication_authorized: bool = False
    external_actions_authorized: bool = False


ExcludeAutoWorkKind = Literal[
    "campaign",
    "software",
    "commercial",
    "legal",
    "seo",
    "analytics",
    "operations",
]

MaestroPlan.model_rebuild()
