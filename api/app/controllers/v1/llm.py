"""LLM controller — provider catalogue + on-demand script generation."""

from fastapi import APIRouter

from app.middleware.verify_token import VerifiedToken
from app.services import llm as llm_service


router = APIRouter()


@router.get("/providers", summary="List LLM providers")
async def list_providers(_: VerifiedToken) -> list[dict]:
    return await llm_service.list_providers()


@router.get("/models", summary="Curated model catalogue for the UI")
async def list_models(_: VerifiedToken) -> list[dict]:
    return await llm_service.list_models()