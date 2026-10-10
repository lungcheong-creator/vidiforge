"""Base controller — provider catalogues, status."""

from fastapi import APIRouter

from app.middleware.verify_token import VerifiedToken
from app.services import llm as llm_service
from app.services import material as material_service
from app.services import voice as voice_service


router = APIRouter()


@router.get("/providers", summary="List all available providers")
async def list_providers(_: VerifiedToken) -> dict:
    """Return LLM / voice / material provider catalogues."""
    return {
        "llm": await llm_service.list_providers(),
        "voice": await voice_service.list_providers(),
        "material": await material_service.list_providers(),
    }


@router.get("/health", summary="Lightweight API health")
async def ping() -> dict:
    return {"ok": True}