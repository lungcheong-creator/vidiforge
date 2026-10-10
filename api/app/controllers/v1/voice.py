"""Voice provider catalogue.

The TTS synthesis endpoints live under /audio; this exposes the provider and
voice catalogue at /voice/providers so the frontend has one place to read it.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.middleware.verify_token import VerifiedToken
from app.services import voice as voice_service


router = APIRouter()


@router.get("/providers", summary="List voice providers and their voices")
async def list_providers(_: VerifiedToken) -> list[dict]:
    return await voice_service.list_providers()
