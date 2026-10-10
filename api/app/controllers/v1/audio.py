"""Audio (TTS-only) controller."""

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.config.config import settings
from app.middleware.verify_token import VerifiedToken
from app.models.schema import AudioRequest
from app.services import voice as voice_service


router = APIRouter()


@router.post("", summary="Synthesize audio from a list of segments")
async def synthesize_audio(request: AudioRequest, _: VerifiedToken) -> dict:
    """Run TTS for the given segments and return their file paths."""
    output_dir = settings.cache_path / "audio"
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        paths = await voice_service.synthesize_script(
            request.segments, request.config, output_dir
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    return {
        "paths": [str(p.relative_to(settings.storage_root.parent)) for p in paths],
        "duration": sum(5.0 for _ in request.segments),
    }


@router.get("/providers", summary="List voice providers")
async def list_providers(_: VerifiedToken) -> list[dict]:
    return await voice_service.list_providers()