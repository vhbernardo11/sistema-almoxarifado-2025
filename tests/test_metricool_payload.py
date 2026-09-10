from __future__ import annotations

import pytest

from integra.publisher.metricool import MetricoolPayloadBuilder
from integra.publisher.models import PublishTarget


def test_instagram_requires_media():
    target = PublishTarget(network="instagram", account_ref="brand", text="Oi")
    with pytest.raises(ValueError, match="Instagram exige"):
        MetricoolPayloadBuilder.build(target)


def test_instagram_payload_marks_ai_content_and_does_not_execute_anything():
    target = PublishTarget(
        network="instagram",
        account_ref="brand",
        text="Conheça o IntegraTrampo",
        media_urls=["https://example.org/post.png"],
        is_ai_generated=True,
    )
    payload = MetricoolPayloadBuilder.build(target)
    assert payload["providers"] == [{"network": "instagram"}]
    assert payload["instagramData"]["isAiGenerated"] is True
    assert payload["media"] == ["https://example.org/post.png"]
