"""LLM controller — provider catalogue + on-demand script generation."""

from fastapi import APIRouter

from app.middleware.verify_token import VerifiedToken
from app.services import llm as llm_service


router = APIRouter()


@router.get("/providers", summary="List LLM providers")
async def list_providers(_: VerifiedToken) -> list[dict]:
    return await llm_service.list_providers()