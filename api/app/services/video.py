"""Video composition via FFmpeg subprocess pipeline.

Pipeline:
  1. Concat all footage clips (re-encoding to libx264 for compatibility)
  2. Mix voice-over track (replace audio)
  3. Mix BGM (lower volume) — concatenated with voice
  4. Burn subtitles via ASS filter
  5. Output H.264 / AAC MP4
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from app.config.config import settings
from app.models.const import AspectRatio
from app.models.exception import TaskError
from app.utils.ffmpeg import get_ffmpeg_binary


def _ffmpeg() -> list[str]:
    return [get_ffmpeg_binary(), "-y", "-hide_banner", "-loglevel", "error"]


def _run(args: list[str], timeout: int = 600) -> subprocess.CompletedProcess:
    """Run ffmpeg with timeout + raise on failure."""
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=True)
    except subprocess.CalledProcessError as e:
        raise TaskError(f"FFmpeg failed: {e.stderr or e.stdout}") from e
    except subprocess.TimeoutExpired as e:
        raise TaskError(f"FFmpeg timed out after {timeout}s") from e


def _aspect_to_resolution(aspect: str) -> tuple[int, int]:
    return {
        AspectRatio.VERTICAL.value: (1080, 1920),
        AspectRatio.HORIZONTAL.value: (1920, 1080),
        AspectRatio.SQUARE.value: (1080, 1080),
    }.get(aspect, (1080, 1920))


def make_concat_manifest(clips: list[Path], manifest_path: Path) -> None:
    """Write an ffmpeg concat demuxer manifest."""
    lines = []
    for clip in clips:
        if clip is None or not clip.is_file():
            continue
        # Use absolute path; escape single quotes
        path_str = str(clip.resolve()).replace("'", "'\\''")
        lines.append(f"file '{path_str}'")
    if not lines:
        raise TaskError("No playable clip files for the concat manifest.")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def concat_clips(
    clips: list[Path | None],
    output_path: Path,
    aspect: str,
    target_duration: float,
) -> Path:
    """Concatenate multiple video clips into one, normalised to target resolution."""
    # Only real files — a Path("") would resolve to the working directory.
    valid = [c for c in clips if c is not None and c.is_file()]
    if not valid:
        raise TaskError("No valid footage clips to concatenate.")

    width, height = _aspect_to_resolution(aspect)
    manifest = output_path.with_suffix(".concat.txt")
    make_concat_manifest(valid, manifest)

    args = _ffmpeg() + [
        "-f", "concat",
        "-safe", "0",
        "-i", str(manifest),
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,format=yuv420p",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-t", str(int(target_duration)),
        "-an",  # drop original audio (will be added later)
        str(output_path),
    ]
    _run(args, timeout=600)
    return output_path


def mix_audio(
    video_path: Path,
    voice_path: Path,
    bgm_path: Path | None,
    output_path: Path,
    bgm_volume: float = 0.3,
) -> Path:
    """Replace the video's audio with voice-over + optional background music."""
    inputs = ["-i", str(video_path), "-i", str(voice_path)]
    has_bgm = bgm_path is not None and bgm_path.is_file()

    args = _ffmpeg() + inputs
    if has_bgm:
        # Loop the BGM to cover the full runtime, duck it, then mix with the voice.
        inputs += ["-i", str(bgm_path)]
        args = _ffmpeg() + inputs + [
            "-filter_complex",
            f"[2:a]aloop=loop=-1:size=2e+09,volume={bgm_volume}[bgm];"
            "[1:a][bgm]amix=inputs=2:duration=shortest:dropout_transition=2[aout]",
            "-map", "0:v:0",
            "-map", "[aout]",
        ]
    else:
        args += ["-map", "0:v:0", "-map", "1:a:0"]

    args += [
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(output_path),
    ]
    _run(args, timeout=300)
    return output_path


def burn_subtitles(
    video_path: Path,
    subtitle_path: Path,
    output_path: Path,
) -> Path:
    """Burn ASS subtitles into the video using the `ass` filter."""
    args = _ffmpeg() + [
        "-i", str(video_path),
        "-vf", f"ass={subtitle_path.resolve()}",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "copy",
        str(output_path),
    ]
    _run(args, timeout=300)
    return output_path


async def compose_full_video(
    *,
    footage_clips: list[Path | None],
    voice_track: Path,
    bgm_path: Path | None,
    subtitle_path: Path,
    aspect: str,
    target_duration: float,
    output_dir: Path,
    work_dir: Path,
) -> Path:
    """End-to-end composition: concat → mix audio → burn subtitles."""
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: concat
    step1 = work_dir / "01_concat.mp4"
    concat_clips(footage_clips, step1, aspect, target_duration)

    # Step 2: mix audio (voice + optional BGM)
    step2 = work_dir / "02_mixed.mp4"
    mix_audio(step1, voice_track, bgm_path, step2)

    # Step 3: burn subtitles
    final_path = output_dir / f"final_{int(target_duration)}s.mp4"
    burn_subtitles(step2, subtitle_path, final_path)

    # Cleanup intermediates
    step1.unlink(missing_ok=True)
    step2.unlink(missing_ok=True)
    # Remove the concat manifest so it can't be mistaken for media
    (work_dir / "01_concat.concat.txt").unlink(missing_ok=True)

    return final_path


async def concatenate_voice_segments(
    segments: list[Path],
    output_path: Path,
) -> Path:
    """Concat multiple mp3 voice segments into a single voice track."""
    valid = [s for s in segments if s is not None and s.is_file()]
    if not valid:
        raise TaskError("No voice segments to concatenate.")

    manifest = output_path.with_suffix(".concat.txt")
    lines = [f"file '{p.resolve()}'" for p in valid]
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")

    args = _ffmpeg() + [
        "-f", "concat",
        "-safe", "0",
        "-i", str(manifest),
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(output_path),
    ]
    _run(args, timeout=120)
    return output_path