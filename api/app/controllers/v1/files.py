"""File serving — stream and download generated media.

Objects are read from the blob store (GCS in production), so they survive
instance restarts. When a signed URL can be produced we redirect the client
straight to GCS, which avoids routing video bytes through Cloud Run.
"""

from __future__ import annotations

import io
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse

from app.config.config import settings
from app.middleware.verify_token import VerifiedToken
from app.services import blobstore


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


def _media_type(key: str) -> str:
    return _MEDIA_TYPES.get(Path(key).suffix.lower(), "application/octet-stream")


def _local_path(key: str) -> Path | None:
    """Resolve a key against the local fallback root, rejecting traversal."""
    if not blobstore.enabled():
        root = settings.storage_root.parent.resolve()
        target = (root / key).resolve()
        try:
            target.relative_to(root)
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Invalid path") from e
        if target.is_file():
            return target
    return None


@router.get("/stream/{path:path}", summary="Stream a media file (inline)")
async def stream_file(path: str, _: VerifiedToken):
    local = _local_path(path)
    if local is not None:
        return FileResponse(local, media_type=_media_type(path), filename=local.name)

    if not blobstore.enabled():
        raise HTTPException(status_code=404, detail="File not found")

    url = blobstore.signed_url(path, minutes=settings.gcs_signed_url_minutes)
    if url:
        return RedirectResponse(url, status_code=302)

    data = blobstore.get_bytes(path)
    if data is None:
        raise HTTPException(status_code=404, detail="File not found")
    return StreamingResponse(io.BytesIO(data), media_type=_media_type(path))


@router.get("/download/{path:path}", summary="Download a media file (attachment)")
async def download_file(path: str, _: VerifiedToken):
    local = _local_path(path)
    if local is not None:
        return FileResponse(
            local,
            media_type="application/octet-stream",
            filename=local.name,
            headers={"Content-Disposition": f'attachment; filename="{local.name}"'},
        )

    if not blobstore.enabled():
        raise HTTPException(status_code=404, detail="File not found")

    name = Path(path).name
    url = blobstore.signed_url(
        path, minutes=settings.gcs_signed_url_minutes, filename=name
    )
    if url:
        return RedirectResponse(url, status_code=302)

    data = blobstore.get_bytes(path)
    if data is None:
        raise HTTPException(status_code=404, detail="File not found")
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )
