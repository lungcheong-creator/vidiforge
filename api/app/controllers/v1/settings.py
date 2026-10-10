"""Settings controller — encrypted API keys and preferences.

Keys are encrypted with Fernet and stored in the blob store (GCS in
production), so they survive instance restarts. Only masked values are ever
returned.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.middleware.verify_token import VerifiedToken
from app.models.schema import ApiKeyBulkSave, ApiKeyEntry, ApiKeySave
from app.services import blobstore
from app.utils import security


log = logging.getLogger("vidiforge.settings")
router = APIRouter()


def _key_path(provider: str) -> str:
    # Provider names are simple slugs; reject anything path-like.
    if "/" in provider or ".." in provider or not provider:
        raise HTTPException(status_code=400, detail="Invalid provider name")
    return f"secrets/{provider}.json"


def _load_all() -> list[dict]:
    out = []
    for path in blobstore.list_keys("secrets/", suffix=".json"):
        rec = blobstore.get_json(path)
        if not rec:
            continue
        provider = rec.get("provider") or path.rsplit("/", 1)[-1].removesuffix(".json")
        try:
            plain = security.decrypt(bytes.fromhex(rec.get("ciphertext", "")))
        except Exception:
            plain = ""
        out.append(
            {
                "provider": provider,
                "masked": security.mask(plain),
                "updated_at": rec.get("updated_at") or datetime.now(timezone.utc).isoformat(),
                "has_value": bool(plain),
            }
        )
    out.sort(key=lambda r: r["provider"])
    return out


def _store(provider: str, value: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    blobstore.put_json(
        _key_path(provider),
        {
            "provider": provider,
            "ciphertext": security.encrypt(value).hex(),
            "updated_at": now,
        },
    )
    return {
        "provider": provider,
        "masked": security.mask(value),
        "updated_at": now,
        "has_value": True,
    }


@router.get("/keys", response_model=list[ApiKeyEntry], summary="List configured API keys (masked)")
async def list_keys(_: VerifiedToken) -> list[ApiKeyEntry]:
    return [ApiKeyEntry(**row) for row in _load_all()]


@router.post("/keys", response_model=ApiKeyEntry, summary="Save or update an API key")
async def save_key(body: ApiKeySave, _: VerifiedToken) -> ApiKeyEntry:
    if not body.value.strip():
        raise HTTPException(status_code=400, detail="Value cannot be empty")
    return ApiKeyEntry(**_store(body.provider, body.value.strip()))


@router.post("/keys/bulk", summary="Save multiple API keys at once")
async def save_keys_bulk(body: ApiKeyBulkSave, _: VerifiedToken) -> dict:
    saved = [_store(p, v.strip())["provider"] for p, v in body.keys.items() if v.strip()]
    return {"ok": True, "saved": saved, "count": len(saved)}


@router.delete("/keys/{provider}", summary="Delete an API key")
async def delete_key(provider: str, _: VerifiedToken) -> dict:
    blobstore.delete_object(_key_path(provider))
    return {"ok": True, "provider": provider}


@router.get("/providers/status", summary="Which providers currently have a key")
async def provider_status(_: VerifiedToken) -> dict:
    return {"configured": [r["provider"] for r in _load_all() if r["has_value"]]}
