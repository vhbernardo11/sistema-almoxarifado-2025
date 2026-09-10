from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from .models import MediaArtifact, MediaIssue, MediaManifest, MediaReviewReport, VideoProbe


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rate_to_float(rate: str | int | float | None) -> float:
    if rate is None:
        return 0.0
    if isinstance(rate, (int, float)):
        return float(rate)
    if "/" in rate:
        num, den = rate.split("/", 1)
        den_f = float(den)
        return float(num) / den_f if den_f else 0.0
    return float(rate)


def probe_video(path: str | Path) -> VideoProbe:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    cmd = [
        "ffprobe", "-v", "error", "-show_streams", "-show_format",
        "-of", "json", str(path),
    ]
    raw = subprocess.check_output(cmd, text=True)
    data = json.loads(raw)
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    if video is None:
        raise ValueError("Arquivo não contém stream de vídeo")
    has_audio = any(s.get("codec_type") == "audio" for s in data.get("streams", []))
    duration = data.get("format", {}).get("duration") or video.get("duration") or 0
    size = data.get("format", {}).get("size") or path.stat().st_size
    return VideoProbe(
        codec=str(video.get("codec_name") or "unknown"),
        width=int(video.get("width") or 0),
        height=int(video.get("height") or 0),
        fps=round(_rate_to_float(video.get("avg_frame_rate") or video.get("r_frame_rate")), 3),
        duration_seconds=round(float(duration), 3),
        size_bytes=int(size),
        has_audio=has_audio,
    )


def _issue(code: str, severity: str, message: str) -> MediaIssue:
    return MediaIssue(code=code, severity=severity, message=message)


def review_media(
    manifest: MediaManifest,
    video_path: str | Path,
    *,
    probe_override: VideoProbe | None = None,
) -> MediaReviewReport:
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(path)
    artifact = MediaArtifact(path=str(path), sha256=sha256_file(path), size_bytes=path.stat().st_size)
    probe = probe_override or probe_video(path)
    issues: list[MediaIssue] = []

    expected = manifest.output
    if probe.width != expected.width or probe.height != expected.height:
        issues.append(_issue(
            "RESOLUTION_MISMATCH", "error",
            f"Esperado {expected.width}x{expected.height}; recebido {probe.width}x{probe.height}.",
        ))

    if expected.format in {"reel", "short", "story"}:
        actual_ratio = probe.width / probe.height if probe.height else 0
        target_ratio = 9 / 16
        if abs(actual_ratio - target_ratio) > 0.015:
            issues.append(_issue("ASPECT_RATIO_INVALID", "error", "Formato vertical 9:16 obrigatório."))

    if abs(probe.fps - expected.fps) > 0.75:
        issues.append(_issue(
            "FPS_MISMATCH", "error", f"Esperado ~{expected.fps} fps; recebido {probe.fps} fps.",
        ))

    duration_tolerance = max(0.8, manifest.expected_duration_seconds * 0.08)
    if abs(probe.duration_seconds - manifest.expected_duration_seconds) > duration_tolerance:
        issues.append(_issue(
            "DURATION_MISMATCH", "error",
            f"Duração esperada {manifest.expected_duration_seconds}s; recebida {probe.duration_seconds}s.",
        ))

    if probe.size_bytes <= 1024:
        issues.append(_issue("FILE_TOO_SMALL", "error", "Arquivo de vídeo parece vazio ou corrompido."))

    if expected.codec == "h264" and probe.codec != "h264":
        issues.append(_issue("CODEC_NONSTANDARD", "warning", f"Codec recebido: {probe.codec}; H.264 é o padrão esperado."))

    if (manifest.music.enabled or manifest.voiceover.enabled) and not probe.has_audio:
        issues.append(_issue("AUDIO_MISSING", "error", "O manifesto exige áudio, mas o arquivo não possui stream de áudio."))

    image_refs = [scene.image for scene in manifest.scenes]
    if len(set(image_refs)) < len(image_refs):
        issues.append(_issue("DUPLICATE_SCENE_ASSET", "warning", "Há cenas reutilizando a mesma arte."))

    last_caption = manifest.scenes[-1].caption.casefold()
    brand = manifest.brand.name.casefold()
    cta = manifest.brand.cta.casefold()
    if brand not in last_caption and cta not in last_caption:
        issues.append(_issue(
            "CTA_NOT_EXPLICIT_IN_FINAL_SCENE", "warning",
            "A cena final não repete explicitamente a marca ou o CTA no campo de legenda do manifesto.",
        ))

    has_error = any(i.severity == "error" for i in issues)
    has_warning = any(i.severity == "warning" for i in issues)
    status = "failed" if has_error else ("warning" if has_warning else "passed")
    return MediaReviewReport(
        campaign_id=manifest.campaign_id,
        status=status,
        ready_for_approval=not has_error,
        artifact=artifact,
        probe=probe,
        expected_duration_seconds=manifest.expected_duration_seconds,
        issues=issues,
    )
