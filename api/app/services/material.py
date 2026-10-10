"""Material (stock footage) service.

Two providers:
  - pexels: free API (https://www.pexels.com/api/), requires key.
  - pixabay: free API (https://pixabay.com/api/), requires key.

For each segment, we hit the API with the keyword and pick the first matching
video clip with the desired orientation. Files are downloaded to cache.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

import httpx

from app.config.config import settings
from app.models.const import MaterialProvider
from app.models.exception import ConfigError, ProviderError
from app.models.schema import MaterialConfig, ScriptSegment


async def _fetch_pexels(keyword: str, orientation: str = "portrait") -> dict | None:
    if not settings.pexels_api_key:
        raise ConfigError("Pexels API key not configured.")
    headers = {"Authorization": settings.pexels_api_key}
    params = {
        "query": keyword,
        "per_page": 5,
        "orientation": orientation,
        "size": "medium",
        "min_duration": 5,
        "max_duration": 30,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            "https://api.pexels.com/videos/search",
            params=params, headers=headers,
        )
    if r.status_code != 200:
        raise ProviderError(f"Pexels error {r.status_code}: {r.text[:200]}")
    data = r.json()
    videos = data.get("videos", [])
    if not videos:
        return None
    # Pick first video, prefer HD file
    for v in videos:
        files = v.get("video_files", [])
        # Find the best matching file
        hd = sorted(
            [f for f in files if f.get("width", 0) >= 720],
            key=lambda f: f.get("width", 0),
            reverse=True,
        )
        if hd:
            return {
                "url": hd[0]["link"],
                "width": hd[0].get("width"),
                "height": hd[0].get("height"),
                "duration": v.get("duration"),
                "title": v.get("name") or keyword,
            }
    return None


async def _fetch_pixabay(keyword: str, orientation: str = "portrait") -> dict | None:
    if not settings.pixabay_api_key:
        raise ConfigError("Pixabay API key not configured.")
    pixabay_orientation = {"portrait": "vertical", "landscape": "horizontal", "square": "all"}.get(orientation, "all")
    params = {
        "key": settings.pixabay_api_key,
        "q": keyword,
        "video_type": "film",
        "per_page": 5,
        "orientation": pixabay_orientation,
        "min_duration": 5,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get("https://pixabay.com/api/videos/", params=params)
    if r.status_code != 200:
        raise ProviderError(f"Pixabay error {r.status_code}: {r.text[:200]}")
    hits = r.json().get("hits", [])
    if not hits:
        return None
    for h in hits:
        videos = h.get("videos", {})
        for quality in ("large", "medium", "small", "tiny"):
            v = videos.get(quality)
            if v:
                return {
                    "url": v["url"],
                    "width": v.get("width"),
                    "height": v.get("height"),
                    "duration": v.get("duration"),
                    "title": h.get("tags", [keyword])[0] if isinstance(h.get("tags"), list) else keyword,
                }
    return None


async def fetch_footage_for_segment(
    segment: ScriptSegment,
    config: MaterialConfig,
    cache_dir: Path,
) -> Path | None:
    """Search & download one stock footage clip for the segment."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    keyword = segment.keyword.strip() or segment.text[:30]
    orientation = config.orientation

    try:
        if config.provider == MaterialProvider.PEXELS:
            hit = await _fetch_pexels(keyword, orientation)
        elif config.provider == MaterialProvider.PIXABAY:
            hit = await _fetch_pixabay(keyword, orientation)
        else:
            raise ConfigError(f"Unsupported material provider: {config.provider}")
    except (ConfigError, ProviderError):
        # Soft-fail: return None → caller will substitute a fallback color clip
        return None

    if not hit:
        return None

    target = cache_dir / f"seg_{segment.id:03d}_{uuid.uuid4().hex[:8]}.mp4"
    try:
        async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
            async with client.stream("GET", hit["url"]) as resp:
                resp.raise_for_status()
                with open(target, "wb") as f:
                    async for chunk in resp.aiter_bytes(chunk_size=64 * 1024):
                        f.write(chunk)
        return target
    except (httpx.HTTPError, OSError):
        return None


async def fetch_footage_for_script(
    segments: list[ScriptSegment],
    config: MaterialConfig,
    cache_dir: Path,
) -> list[Path]:
    """Fetch footage for all segments (sequential to avoid rate limits)."""
    paths: list[Path] = []
    for seg in segments:
        path = await fetch_footage_for_segment(seg, config, cache_dir)
        paths.append(path) if path else paths.append(Path(""))  # type: ignore[arg-type]
    return paths


async def list_providers() -> list[dict[str, Any]]:
    catalogue = [
        {
            "id": "pexels",
            "name": "Pexels",
            "requires_key": True,
            "available": bool(settings.pexels_api_key),
            "endpoint": "https://www.pexels.com/api/",
        },
        {
            "id": "pixabay",
            "name": "Pixabay",
            "requires_key": True,
            "available": bool(settings.pixabay_api_key),
            "endpoint": "https://pixabay.com/api/",
        },
    ]
    for c in catalogue:
        c["active"] = settings.material_provider == c["id"]
    return catalogue