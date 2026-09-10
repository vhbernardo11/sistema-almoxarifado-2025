from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ResumeState(BaseModel):
    """Estado suficiente para entender de onde uma execução pode continuar."""

    run_id: str
    run_status: str
    current_stage: str | None = None
    checkpoint_key: str | None = None
    resume_sequence: int | None = None
    snapshot: dict[str, Any] = Field(default_factory=dict)
    completed_sequences: list[int] = Field(default_factory=list)
    unfinished_sequences: list[int] = Field(default_factory=list)
