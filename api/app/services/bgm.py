"""Background music selection."""

from __future__ import annotations

import os
import random
from pathlib import Path

from app.config.config import settings
from app.models.schema import BGMConfig


def list_bgm(songs_dir: Path | None = None) -> list[Path]:
    """List all audio files in the default songs directory."""
    songs_dir = songs_dir or (settings.storage_root / ".." / "resource" / "songs")
    songs_dir = songs_dir.resolve()
    if not songs_dir.exists():
        return []
    exts = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}
    return sorted(p for p in songs_dir.iterdir() if p.suffix.lower() in exts and p.is_file())


def pick_random_bgm() -> Path | None:
    """Pick a random BGM track from the songs directory."""
    tracks = list_bgm()
    return random.choice(tracks) if tracks else None


def pick_bgm(config: BGMConfig) -> Path | None:
    """Pick a BGM track according to the config (explicit path > random)."""
    if not config.enabled:
        return None
    if config.path:
        p = Path(config.path)
        return p if p.exists() else pick_random_bgm()
    return pick_random_bgm()