from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

Network = Literal["instagram", "facebook", "linkedin", "youtube", "tiktok", "twitter", "bluesky", "threads", "gmb"]
ContentType = Literal["post", "reel", "story", "short", "video"]


class PublishTarget(BaseModel):
    network: Network
    content_type: ContentType = "post"
    account_ref: str
    text: str = ""
    media_urls: list[HttpUrl] = Field(default_factory=list)
    scheduled_for: datetime | None = None
    timezone: str = "America/Sao_Paulo"
    is_ai_generated: bool = False


class PublicationReceipt(BaseModel):
    provider: str
    external_id: str | None = None
    planner_url: HttpUrl | None = None
    status: str
    executed_at: datetime | None = None


class PublicationRecord(BaseModel):
    id: str
    run_id: str
    approval_id: str
    provider: str
    target: dict
    status: str
    external_id: str | None = None
    planner_url: str | None = None
    error: str | None = None
    attempted_at: datetime | None = None
    created_at: datetime | None = None


class PublisherResult(BaseModel):
    run_id: str
    approval_id: str
    publication_id: str | None = None
    ready: bool
    publication_attempted: bool = False
    external_actions_performed: bool = False
    receipt: PublicationReceipt | None = None
    reason: str | None = None
