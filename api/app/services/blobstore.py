"""GCS-backed blob store.

All durable state lives here so the service survives instance restarts and
works correctly with more than one Cloud Run instance:

    tasks/<task_id>/task.json      task metadata
    tasks/<task_id>/output.mp4     rendered video
    tasks/<task_id>/assets/...     per-task intermediates we choose to keep
    secrets/<provider>.json        encrypted BYOK API keys

When ``GCS_BUCKET`` is unset (local development) every call falls back to the
local filesystem under ``storage/`` so nothing needs a bucket to run.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from datetime import timedelta
from pathlib import Path
from typing import Any

from app.config.config import settings

log = logging.getLogger("vidiforge.blobstore")

_client = None
_client_lock = threading.Lock()

# Small in-process cache so list/get don't hammer GCS on every poll.
_cache: dict[str, tuple[float, Any]] = {}
_CACHE_TTL = 5.0


def enabled() -> bool:
    return bool(settings.gcs_bucket)


def _bucket_name() -> str:
    return settings.gcs_bucket


def _get_client():
    global _client
    if _client is not None:
        return _client
    with _client_lock:
        if _client is None:
            from google.cloud import storage  # imported lazily

            _client = storage.Client()
    return _client


def _bucket():
    return _get_client().bucket(_bucket_name())


def _local_root() -> Path:
    root = settings.storage_root
    root.mkdir(parents=True, exist_ok=True)
    return root


# ---------------------------------------------------------------- raw objects


def put_bytes(key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    if enabled():
        blob = _bucket().blob(key)
        blob.upload_from_string(data, content_type=content_type)
    else:
        target = _local_root() / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    _cache.pop(key, None)
    return key


def get_bytes(key: str) -> bytes | None:
    if enabled():
        blob = _bucket().blob(key)
        if not blob.exists():
            return None
        return blob.download_as_bytes()
    target = _local_root() / key
    return target.read_bytes() if target.is_file() else None


def delete_object(key: str) -> bool:
    """Delete a single object. Returns True when something was removed."""
    removed = False
    if enabled():
        blob = _bucket().blob(key)
        if blob.exists():
            blob.delete()
            removed = True
    else:
        target = _local_root() / key
        if target.is_file():
            target.unlink()
            removed = True
    _cache.pop(key, None)
    return removed


def delete_prefix(prefix: str) -> int:
    """Delete every object under `prefix` (a folder path). Returns the count."""
    removed = 0
    if enabled():
        for blob in _get_client().list_blobs(_bucket_name(), prefix=prefix):
            blob.delete()
            removed += 1
    else:
        target = _local_root() / prefix.rstrip("/")
        if target.is_dir():
            import shutil

            removed = sum(1 for p in target.rglob("*") if p.is_file())
            shutil.rmtree(target, ignore_errors=True)
        elif target.is_file():
            target.unlink()
            removed = 1
    for k in [k for k in _cache if k.startswith(prefix.rstrip("/"))]:
        _cache.pop(k, None)
    return removed


def upload_file(local_path: Path, key: str, content_type: str | None = None) -> str:
    """Upload a local file to `key`."""
    if not local_path.is_file():
        raise FileNotFoundError(local_path)
    if enabled():
        blob = _bucket().blob(key)
        blob.upload_from_filename(str(local_path), content_type=content_type)
    else:
        target = _local_root() / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(local_path.read_bytes())
    _cache.pop(key, None)
    return key


def signed_url(key: str, minutes: int = 60, filename: str | None = None) -> str | None:
    """Return a time-limited download URL, or None when not on GCS."""
    if not enabled():
        return None
    try:
        blob = _bucket().blob(key)
        params = {"response_disposition": f'attachment; filename="{filename}"'} if filename else None
        return blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=minutes),
            method="GET",
            response_disposition=params["response_disposition"] if params else None,
        )
    except Exception as e:  # signing needs a private key; ADC on Cloud Run has one
        log.warning("signed_url failed for %s: %s", key, e)
        return None


# --------------------------------------------------------------------- JSON


def put_json(key: str, obj: Any) -> None:
    put_bytes(key, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json")
    _cache[key] = (time.time(), obj)


def get_json(key: str, use_cache: bool = True) -> Any | None:
    if use_cache:
        hit = _cache.get(key)
        if hit and time.time() - hit[0] < _CACHE_TTL:
            return hit[1]
    raw = get_bytes(key)
    if raw is None:
        return None
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return None
    _cache[key] = (time.time(), obj)
    return obj


def list_keys(prefix: str, suffix: str = "") -> list[str]:
    """List object names under `prefix` (optionally filtered by suffix)."""
    if enabled():
        names = [
            b.name
            for b in _get_client().list_blobs(_bucket_name(), prefix=prefix)
            if b.name.endswith(suffix)
        ]
    else:
        root = _local_root()
        base = root / prefix
        names = []
        if base.exists():
            for p in base.rglob("*"):
                if p.is_file():
                    rel = str(p.relative_to(root))
                    if rel.endswith(suffix):
                        names.append(rel)
    return sorted(names)
