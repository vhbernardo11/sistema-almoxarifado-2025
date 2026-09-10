from __future__ import annotations

from datetime import datetime
from typing import Any

from .models import MediaManifest, MediaReviewReport


class MediaPublicationError(RuntimeError):
    pass


def build_publication_candidate(
    *,
    manifest: MediaManifest,
    review: MediaReviewReport,
    account_ref: str,
    text: str,
    media_url: str,
    network: str = "instagram",
    content_type: str = "reel",
    scheduled_for: datetime | None = None,
    timezone: str = "America/Sao_Paulo",
) -> dict[str, Any]:
    if not review.ready_for_approval:
        raise MediaPublicationError("Mídia reprovada pelo QA; publicação bloqueada.")
    if not media_url.startswith(("https://", "http://")):
        raise MediaPublicationError("O Publisher exige URL pública da mídia; caminho local não é publicável.")
    return {
        "network": network,
        "content_type": content_type,
        "account_ref": account_ref,
        "text": text,
        "media_urls": [media_url],
        "scheduled_for": scheduled_for.isoformat() if scheduled_for else None,
        "timezone": timezone,
        "is_ai_generated": manifest.is_ai_generated,
    }


def build_approval_payload(
    *,
    run_id: str,
    manifest: MediaManifest,
    review: MediaReviewReport,
    publication_candidate: dict[str, Any],
) -> dict[str, Any]:
    if not review.ready_for_approval:
        raise MediaPublicationError("Não é possível solicitar aprovação para mídia reprovada.")
    return {
        "run_id": run_id,
        "campaign_id": manifest.campaign_id,
        "brand": manifest.brand.model_dump(mode="json"),
        "publication": publication_candidate,
        "media": {
            "sha256": review.artifact.sha256,
            "size_bytes": review.artifact.size_bytes,
            "codec": review.probe.codec,
            "width": review.probe.width,
            "height": review.probe.height,
            "duration_seconds": review.probe.duration_seconds,
        },
        "qa": {
            "status": review.status,
            "review_scope": review.review_scope,
            "issues": [issue.model_dump(mode="json") for issue in review.issues],
        },
    }
