from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from .models import MediaManifest


class MediaRenderError(RuntimeError):
    pass


def _motion_expr(motion: str) -> str:
    if motion == "zoom_in":
        return "zoompan=z='min(zoom+0.0015,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    if motion == "zoom_out":
        return "zoompan=z='if(lte(on,1),1.12,max(1.0,zoom-0.0012))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    if motion == "pan_left":
        return "zoompan=z='1.05':x='max(0,iw*0.04-on*1.2)':y='ih/2-(ih/zoom/2)'"
    if motion == "pan_right":
        return "zoompan=z='1.05':x='min(iw*0.04,on*1.2)':y='ih/2-(ih/zoom/2)'"
    return "zoompan=z='1.0':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"


class FFmpegMediaRenderer:
    def __init__(self, *, ffmpeg_binary: str = "ffmpeg"):
        self.ffmpeg_binary = ffmpeg_binary

    def render(self, *, manifest: MediaManifest, asset_root: str | Path, output_path: str | Path) -> Path:
        root = Path(asset_root)
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        width, height, fps = manifest.output.width, manifest.output.height, manifest.output.fps
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            clips: list[Path] = []
            for index, scene in enumerate(manifest.scenes, start=1):
                image = (root / scene.image).resolve()
                if not image.exists():
                    raise MediaRenderError(f"Asset ausente: {image}")
                clip = tmpdir / f"scene_{index:02d}.mp4"
                frames = max(int(scene.duration_seconds * fps), 1)
                vf = (
                    f"scale={width}:{height}:force_original_aspect_ratio=increase,"
                    f"crop={width}:{height},{_motion_expr(scene.motion)}:"
                    f"d={frames}:s={width}x{height}:fps={fps},"
                    f"trim=duration={scene.duration_seconds},setpts=PTS-STARTPTS,format=yuv420p"
                )
                subprocess.run([
                    self.ffmpeg_binary, "-y", "-loop", "1", "-t", str(scene.duration_seconds),
                    "-i", str(image), "-vf", vf, "-r", str(fps), "-pix_fmt", "yuv420p",
                    "-c:v", "libx264", str(clip),
                ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                clips.append(clip)
            concat = tmpdir / "concat.txt"
            concat.write_text("".join(f"file '{p}'\n" for p in clips), encoding="utf-8")
            subprocess.run([
                self.ffmpeg_binary, "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
                "-c", "copy", "-movflags", "+faststart", str(output),
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output
