from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

ReviewDecision = Literal["pending", "accepted", "changes_requested", "rejected"]


class WorkflowReview(BaseModel):
    id: str
    job_id: str
    test_actor_id: str
    route: str
    payload_digest: str
    review_payload: dict[str, Any] = Field(default_factory=dict)
    decision: ReviewDecision = "pending"
    reviewer: str | None = None
    note: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    publication_authorized: bool = False
    external_actions_authorized: bool = False
    created_at: datetime | None = None
    decided_at: datetime | None = None
