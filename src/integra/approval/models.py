from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ApprovalDecision = Literal["pending", "approved", "changes_requested", "rejected"]


class ApprovalRecord(BaseModel):
    id: str
    run_id: str
    content_digest: str
    decision: ApprovalDecision = "pending"
    approver: str | None = None
    note: str | None = None
    created_at: datetime | None = None
    decided_at: datetime | None = None
    metadata: dict = Field(default_factory=dict)
