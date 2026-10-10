"""File serving endpoints — stream and download generated media.

Mounted at the API root (`/api/v1/...`) so output URLs are stable and short,
e.g. `/api/v1/download/storage/outputs/<task>/final_19s.mp4`.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config.config import settings
from app.middleware.verify_token import VerifiedToken


router = APIRouter()

_MEDIA_TYPES = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".ass": "text/plain; charset=utf-8",
    ".srt": "text/plain; charset=utf-8",
}


def _resolve_safe(path: str) -> Path:
    """Resolve `path` under the project root, rejecting traversal attempts."""
    root = settings.storage_root.parent.resolve()
    target = (root / path).resolve()
    try:
        target.relative_to(root)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid path") from e
    if not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return target


@router.get("/stream/{path:path}", summary="Stream a media file (inline)")
async def stream_file(path: str, _: VerifiedToken) -> FileResponse:
    target = _resolve_safe(path)
    media_type = _MEDIA_TYPES.get(target.suffix.lower(), "application/octet-stream")
    return FileResponse(target, media_type=media_type, filename=target.name)


@router.get("/download/{path:path}", summary="Download a media file (attachment)")
async def download_file(path: str, _: VerifiedToken) -> FileResponse:
    target = _resolve_safe(path)
    return FileResponse(
        target,
        media_type="application/octet-stream",
        filename=target.name,
        headers={"Content-Disposition": f'attachment; filename="{target.name}"'},
    )
