"""Subtitle-only controller."""

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.config.config import settings
from app.middleware.verify_token import VerifiedToken
from app.models.schema import SubtitleRequest
from app.services import subtitle as subtitle_service


router = APIRouter()


@router.post("", summary="Generate subtitle file for a script")
async def generate_subtitle(request: SubtitleRequest, _: VerifiedToken) -> dict:
    voice_paths = [Path(p) for p in request.voice_paths]
    output_dir = settings.cache_path / "subtitle"
    output_ass = output_dir / "out.ass"

    try:
        cues, path = await subtitle_service.generate_subtitles_for_segments(
            segments=request.script.segments,
            voice_paths=voice_paths,
            config=request.config,
            output_ass_path=output_ass,
            language="zh",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    return {
        "path": str(path.relative_to(settings.storage_root.parent)),
        "cues": [{"start": c.start, "end": c.end, "text": c.text} for c in cues],
        "srt": subtitle_service.cues_to_srt(cues),
    }