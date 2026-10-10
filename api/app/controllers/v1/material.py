"""Material (stock footage) endpoints — upload + list providers."""

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config.config import settings
from app.middleware.verify_token import VerifiedToken
from app.services import material as material_service


router = APIRouter()


@router.post("/upload", summary="Upload a local video/image asset")
async def upload_material(
    file: UploadFile = File(...),
    _: VerifiedToken = None,
) -> dict:
    """Store an uploaded file in the upload directory and return its ID."""
    upload_dir = settings.upload_path
    upload_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename or "").suffix.lower() or ".mp4"
    if suffix not in {".mp4", ".mov", ".webm", ".jpg", ".jpeg", ".png"}:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    asset_id = uuid.uuid4().hex
    target = upload_dir / f"{asset_id}{suffix}"

    with open(target, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {
        "asset_id": asset_id,
        "path": str(target.relative_to(settings.storage_root.parent)),
        "url": f"/api/v1/stream/{target.relative_to(settings.storage_root.parent)}",
        "filename": file.filename,
        "size": target.stat().st_size,
    }


@router.get("/providers", summary="List material providers")
async def list_providers(_: VerifiedToken) -> list[dict]:
    return await material_service.list_providers()