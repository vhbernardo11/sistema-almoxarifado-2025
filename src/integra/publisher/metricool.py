from __future__ import annotations

from typing import Any

from .models import PublishTarget


class MetricoolPayloadBuilder:
    """Traduz PublishTarget para o contrato esperado pelo conector Metricool.

    Este módulo não chama a rede. A chamada externa permanece separada para que
    o ApprovalGate seja sempre verificado antes do adaptador.
    """

    @staticmethod
    def build(target: PublishTarget) -> dict[str, Any]:
        if target.network == "instagram" and not target.media_urls:
            raise ValueError("Instagram exige pelo menos uma imagem ou vídeo")
        if target.content_type in {"reel", "short", "video"} and not target.media_urls:
            raise ValueError("Conteúdo em vídeo exige media_urls")

        info: dict[str, Any] = {
            "autoPublish": True,
            "draft": False,
            "descendants": [],
            "firstCommentText": "",
            "hasNotReadNotes": False,
            "media": [str(url) for url in target.media_urls],
            "mediaAltText": [],
            "providers": [{"network": target.network}],
            "shortener": False,
            "smartLinkData": {"ids": []},
            "text": target.text,
        }
        if target.scheduled_for:
            info["publicationDate"] = {
                "dateTime": target.scheduled_for.replace(tzinfo=None).isoformat(timespec="seconds"),
                "timezone": target.timezone,
            }
        if target.network == "instagram":
            type_map = {"post": "POST", "reel": "REEL", "story": "STORY"}
            info["instagramData"] = {
                "type": type_map.get(target.content_type, "POST"),
                "showReelOnFeed": True,
                "isAiGenerated": target.is_ai_generated,
            }
        return info
