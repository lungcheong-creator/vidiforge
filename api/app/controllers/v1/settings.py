"""Settings controller — encrypted API key CRUD."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import select

from app.config.config import settings
from app.db.database import session_scope
from app.db.models import ApiKey
from app.middleware.verify_token import VerifiedToken
from app.models.schema import ApiKeyBulkSave, ApiKeyEntry, ApiKeySave
from app.utils import security


router = APIRouter()


@router.get("/keys", response_model=list[ApiKeyEntry], summary="List configured API keys (masked)")
async def list_keys(_: VerifiedToken) -> list[ApiKeyEntry]:
    """Return all stored keys with masked values."""
    with session_scope() as s:
        rows = s.exec(select(ApiKey)).all()
    out = []
    for r in rows:
        plain = security.decrypt(r.ciphertext) if r.ciphertext else ""
        out.append(ApiKeyEntry(
            provider=r.provider,
            masked=security.mask(plain),
            updated_at=r.updated_at,
            has_value=bool(plain),
        ))
    return out


@router.post("/keys", summary="Save or update an API key (encrypted at rest)")
async def save_key(body: ApiKeySave, _: VerifiedToken) -> ApiKeyEntry:
    """Save a single API key, encrypted with VIDIFORGE_MASTER_KEY."""
    if not body.value.strip():
        raise HTTPException(status_code=400, detail="Value cannot be empty")

    ciphertext = security.encrypt(body.value)
    now = datetime.now(timezone.utc)
    with session_scope() as s:
        existing = s.get(ApiKey, body.provider)
        if existing:
            existing.ciphertext = ciphertext
            existing.updated_at = now
            s.add(existing)
        else:
            s.add(ApiKey(provider=body.provider, ciphertext=ciphertext, updated_at=now))
        s.commit()

    return ApiKeyEntry(
        provider=body.provider,
        masked=security.mask(body.value),
        updated_at=now,
        has_value=True,
    )


@router.post("/keys/bulk", summary="Save multiple API keys at once")
async def save_keys_bulk(body: ApiKeyBulkSave, _: VerifiedToken) -> dict:
    """Save multiple keys in one request."""
    now = datetime.utcnow()
    saved = []
    for provider, value in body.keys.items():
        if not value.strip():
            continue
        ciphertext = security.encrypt(value)
        with session_scope() as s:
            existing = s.get(ApiKey, provider)
            if existing:
                existing.ciphertext = ciphertext
                existing.updated_at = now
                s.add(existing)
            else:
                s.add(ApiKey(provider=provider, ciphertext=ciphertext, updated_at=now))
            s.commit()
        saved.append(provider)
    return {"ok": True, "saved": saved, "count": len(saved)}


@router.delete("/keys/{provider}", summary="Delete an API key")
async def delete_key(provider: str, _: VerifiedToken) -> dict:
    with session_scope() as s:
        row = s.get(ApiKey, provider)
        if row:
            s.delete(row)
            s.commit()
    return {"ok": True, "provider": provider}


# ---- File streaming & download ----

class StreamResponse(BaseModel):
    ok: bool


@router.get("/stream/{path:path}", summary="Stream a media file from storage")
async def stream_file(path: str, _: VerifiedToken):
    """Serve a media file from storage with proper Content-Type.

    The path is validated to prevent traversal attacks.
    """
    from fastapi.responses import FileResponse

    # Resolve and check path safety
    storage_root = settings.storage_root.parent.resolve()
    target = (storage_root / path).resolve()
    try:
        target.relative_to(storage_root)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid path") from e
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    media_type = "video/mp4"
    if target.suffix == ".mp3":
        media_type = "audio/mpeg"
    elif target.suffix in {".jpg", ".jpeg"}:
        media_type = "image/jpeg"
    elif target.suffix == ".png":
        media_type = "image/png"
    elif target.suffix == ".ass":
        media_type = "text/plain"

    return FileResponse(target, media_type=media_type, filename=target.name)


@router.get("/download/{path:path}", summary="Download a media file (forces attachment)")
async def download_file(path: str, _: VerifiedToken):
    """Serve a media file with Content-Disposition: attachment."""
    from fastapi.responses import FileResponse

    storage_root = settings.storage_root.parent.resolve()
    target = (storage_root / path).resolve()
    try:
        target.relative_to(storage_root)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid path") from e
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        target, media_type="application/octet-stream", filename=target.name,
        headers={"Content-Disposition": f'attachment; filename="{target.name}"'},
    )