from pathlib import Path

import pytest

from integra.media.bridge import MediaPublicationError, build_approval_payload, build_publication_candidate
from integra.media.models import AudioSpec, BrandSpec, MediaManifest, MediaOutputSpec, SceneSpec, VideoProbe
from integra.media.reviewer import review_media
from integra.media.templates import available_templates, build_template


def manifest() -> MediaManifest:
    return MediaManifest(
        campaign_id="demo",
        brand=BrandSpec(name="IntegraTrampo", cta="Cadastre-se"),
        output=MediaOutputSpec(format="reel", width=1080, height=1920, fps=30),
        scenes=[
            SceneSpec(id="1", image="a.png", duration_seconds=3.0, caption="Oportunidade"),
            SceneSpec(id="2", image="b.png", duration_seconds=3.0, caption="Conecte-se"),
            SceneSpec(id="3", image="c.png", duration_seconds=4.0, caption="Conheça o IntegraTrampo"),
        ],
    )


def fake_video(tmp_path: Path) -> Path:
    path = tmp_path / "video.mp4"
    path.write_bytes(b"0" * 4096)
    return path


def good_probe(**changes) -> VideoProbe:
    values = dict(codec="h264", width=1080, height=1920, fps=30.0, duration_seconds=10.0, size_bytes=4096, has_audio=False)
    values.update(changes)
    return VideoProbe(**values)


def test_valid_media_is_ready_for_approval(tmp_path):
    report = review_media(manifest(), fake_video(tmp_path), probe_override=good_probe())
    assert report.ready_for_approval is True
    assert report.status == "passed"
    assert len(report.artifact.sha256) == 64


def test_wrong_resolution_fails_closed(tmp_path):
    report = review_media(manifest(), fake_video(tmp_path), probe_override=good_probe(width=1280, height=720))
    assert report.ready_for_approval is False
    assert report.status == "failed"
    assert {issue.code for issue in report.issues} >= {"RESOLUTION_MISMATCH", "ASPECT_RATIO_INVALID"}


def test_audio_required_but_missing_fails(tmp_path):
    data = manifest()
    data.voiceover = AudioSpec(enabled=True)
    report = review_media(data, fake_video(tmp_path), probe_override=good_probe(has_audio=False))
    assert report.ready_for_approval is False
    assert "AUDIO_MISSING" in {issue.code for issue in report.issues}


def test_publication_candidate_requires_public_url(tmp_path):
    report = review_media(manifest(), fake_video(tmp_path), probe_override=good_probe())
    with pytest.raises(MediaPublicationError):
        build_publication_candidate(
            manifest=manifest(), review=report, account_ref="brand-1", text="Teste", media_url="/tmp/video.mp4"
        )


def test_approval_payload_binds_exact_media_hash(tmp_path):
    data = manifest()
    report = review_media(data, fake_video(tmp_path), probe_override=good_probe())
    candidate = build_publication_candidate(
        manifest=data, review=report, account_ref="brand-1", text="Teste", media_url="https://example.com/video.mp4"
    )
    payload = build_approval_payload(run_id="run-1", manifest=data, review=report, publication_candidate=candidate)
    assert payload["media"]["sha256"] == report.artifact.sha256
    assert payload["qa"]["status"] == "passed"
    assert payload["publication"]["media_urls"] == ["https://example.com/video.mp4"]


def test_three_templates_are_available():
    ids = available_templates()
    assert set(ids) == {"professional_opportunity", "service_demand", "business_recruitment"}
    built = build_template("service_demand", profession="Eletricista")
    assert built.output.format == "reel"
    assert len(built.scenes) == 3
    assert "IntegraTrampo" in built.scenes[-1].caption
