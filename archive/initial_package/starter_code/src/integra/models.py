from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field

Status = Literal["pending", "running", "completed", "failed", "waiting_approval"]

class Artifact(BaseModel):
    id: str
    type: str
    path_or_url: str
    metadata: dict[str, Any] = Field(default_factory=dict)

class AgentResult(BaseModel):
    agent_id: str
    status: Status
    summary: str
    data: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[Artifact] = Field(default_factory=list)

class Task(BaseModel):
    id: str
    agent_id: str
    objective: str
    status: Status = "pending"
    result: AgentResult | None = None

class Run(BaseModel):
    id: str
    goal: str
    status: Status = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tasks: list[Task] = Field(default_factory=list)
