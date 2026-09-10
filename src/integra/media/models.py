from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

MediaFormat = Literal["reel", "short", "story", "post_video"]
Motion = Literal["zoom_in", "zoom_out", "pan_left", "pan_right", "static"]
ReviewStatus = Literal["passed", "warning", "failed"]
IssueSeverity = Literal["warning", "error"]


class BrandSpec(BaseModel):
    name: str = Field(min_length=1)
    cta: str = Field(min_length=1)
    tagline: str = ""


class AudioSpec(BaseModel):
    enabled: bool = False
    notes: str = ""


class MediaOutputSpec(BaseModel):
    format: MediaFormat = "reel"
    width: int = Field(default=1080, ge=720)
    height: int = Field(default=1920, ge=1280)
    fps: int = Field(default=30, ge=24, le=60)
    codec: str = "h264"


class SceneSpec(BaseModel):
    id: str = Field(min_length=1)
    image: str = Field(min_length=1)
    duration_seconds: float = Field(gt=0)
    motion: Motion = "static"
    caption: str = ""
    asset_sha256: str | None = None


class MediaManifest(BaseModel):
    campaign_id: str = Field(min_length=1)
    brand: BrandSpec
    output: MediaOutputSpec = Field(default_factory=MediaOutputSpec)
    music: AudioSpec = Field(default_factory=AudioSpec)
    voiceover: AudioSpec = Field(default_factory=AudioSpec)
    scenes: list[SceneSpec] = Field(min_length=1)
    is_ai_generated: bool = True

    @property
    def expected_duration_seconds(self) -> float:
        return round(sum(scene.duration_seconds for scene in self.scenes), 3)


class VideoProbe(BaseModel):
    codec: str
    width: int
    height: int
    fps: float
    duration_seconds: float
    size_bytes: int
    has_audio: bool = False


class MediaArtifact(BaseModel):
    path: str
    sha256: str
    size_bytes: int


class MediaIssue(BaseModel):
    code: str
    severity: IssueSeverity
    message: str


class MediaReviewReport(BaseModel):
    campaign_id: str
    status: ReviewStatus
    ready_for_approval: bool
    artifact: MediaArtifact
    probe: VideoProbe
    expected_duration_seconds: float
    issues: list[MediaIssue] = Field(default_factory=list)
    review_scope: str = "artifact_and_metadata"
