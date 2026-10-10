"""FFmpeg binary resolver and probe utilities."""

from __future__ import annotations

import os
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

from app.models.exception import ConfigError


@lru_cache(maxsize=1)
def get_ffmpeg_binary() -> str:
    """Return the absolute path of the FFmpeg executable.

    Resolution order:
      1. ``[app].ffmpeg_path`` in ``settings.toml`` (if it exists and is executable)
      2. ``IMAGEIO_FFMPEG_EXE`` environment variable
      3. ``FFMPEG_PATH`` environment variable
      4. ``shutil.which("ffmpeg")`` from PATH
    """

    candidates: list[Path | str] = []
    settings_file = Path(__file__).resolve().parents[1] / "config" / "settings.toml"
    if settings_file.exists():
        try:
            import tomllib  # py3.11+
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]
        with open(settings_file, "rb") as f:
            data = tomllib.load(f)
        custom = data.get("app", {}).get("ffmpeg_path")
        if custom:
            candidates.append(custom)

    for env_var in ("IMAGEIO_FFMPEG_EXE", "FFMPEG_PATH"):
        val = os.environ.get(env_var)
        if val:
            candidates.append(val)

    candidates.append("ffmpeg")  # PATH lookup

    for cand in candidates:
        path = Path(cand) if not isinstance(cand, str) else Path(cand)
        if path.is_file() and os.access(path, os.X_OK):
            return str(path.resolve())
        resolved = shutil.which(str(cand))
        if resolved:
            return resolved

    raise ConfigError(
        "FFmpeg binary not found. Install ffmpeg (apt-get install ffmpeg) "
        "or set IMAGEIO_FFMPEG_EXE / FFMPEG_PATH env var."
    )


def _get_ffprobe_binary() -> str:
    """Locate ffprobe, preferring one sitting next to the resolved ffmpeg."""
    try:
        sibling = Path(get_ffmpeg_binary()).parent / "ffprobe"
        if sibling.is_file() and os.access(sibling, os.X_OK):
            return str(sibling)
    except ConfigError:
        pass
    return shutil.which("ffprobe") or "ffprobe"


def probe_duration(path: str | Path) -> float:
    """Return the duration (seconds) of a media file via ffprobe.

    Returns 0.0 when ffprobe is unavailable or the file is unreadable.
    """
    try:
        out = subprocess.run(
            [
                _get_ffprobe_binary(), "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True, text=True, timeout=30, check=True,
        )
        return float(out.stdout.strip() or "0")
    except (subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired, OSError):
        return 0.0


def probe_resolution(path: str | Path) -> tuple[int, int]:
    """Return (width, height) of a video file via ffprobe, or (0, 0)."""
    try:
        out = subprocess.run(
            [
                _get_ffprobe_binary(), "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=s=x:p=0",
                str(path),
            ],
            capture_output=True, text=True, timeout=30, check=True,
        )
        w, h = out.stdout.strip().split("x")
        return int(w), int(h)
    except (subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired, OSError):
        return (0, 0)