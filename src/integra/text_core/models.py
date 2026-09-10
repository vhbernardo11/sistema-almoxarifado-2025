from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class CampaignRequest(BaseModel):
    """Entrada canônica do núcleo textual do IntegraSquad."""

    goal: str = Field(min_length=8)
    audience: str | None = None
    location: str | None = None
    channel: str = "instagram"
    tone: str = "claro, humano e comercial"
    constraints: list[str] = Field(default_factory=list)


class ResearchSource(BaseModel):
    title: str
    url: HttpUrl
    note: str


class ResearchBrief(BaseModel):
    objective: str
    audience_insights: list[str]
    market_context: list[str]
    opportunities: list[str]
    risks: list[str]
    facts_to_use: list[str]
    sources: list[ResearchSource]
    confidence: Literal["low", "medium", "high"]


class StrategyBrief(BaseModel):
    objective: str
    positioning: str
    core_message: str
    promise: str
    proof_points: list[str]
    objections: list[str]
    content_angle: str
    call_to_action: str
    guardrails: list[str] = Field(default_factory=list)


class CopyPackage(BaseModel):
    headline: str
    primary_copy: str
    short_caption: str
    long_caption: str
    call_to_action: str
    hashtags: list[str] = Field(default_factory=list)
    visual_brief: str
    claims_used: list[str] = Field(default_factory=list)


class TextCoreResult(BaseModel):
    request: CampaignRequest
    research: ResearchBrief
    strategy: StrategyBrief
    copy: CopyPackage
    publication_authorized: bool = False
