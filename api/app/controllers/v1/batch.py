"""Batch endpoints — create, list, inspect, run and delete batches."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from app.middleware.verify_token import VerifiedToken
from app.models.schema import (
    AspectRatio,
    BGMConfig,
    Language,
    LLMProvider,
    MaterialConfig,
    SubtitleConfig,
    VoiceConfig,
)
from app.services import batch as batch_service


router = APIRouter()


class BatchCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    topics: list[str] = Field(..., min_length=1, max_length=100)
    # Template applied to every topic; only `topic` is replaced per item.
    language: Language = Language.ZH
    aspect: AspectRatio = AspectRatio.VERTICAL
    duration: int = Field(default=30, ge=5, le=180)
    segments: int = Field(default=5, ge=1, le=20)
    llm_provider: LLMProvider = LLMProvider.DEEPSEEK
    llm_model: str = "deepseek-flash"
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    subtitle: SubtitleConfig = Field(default_factory=SubtitleConfig)
    material: MaterialConfig = Field(default_factory=MaterialConfig)
    bgm: BGMConfig = Field(default_factory=BGMConfig)


def _template(body: BatchCreate) -> dict[str, Any]:
    return {
        "keywords": [],
        "language": body.language.value,
        "aspect": body.aspect.value,
        "duration": body.duration,
        "segments": body.segments,
        "llm_provider": body.llm_provider.value,
        "llm_model": body.llm_model,
        "script": None,
        "voice": body.voice.model_dump(mode="json"),
        "subtitle": body.subtitle.model_dump(mode="json"),
        "material": body.material.model_dump(mode="json"),
        "bgm": body.bgm.model_dump(mode="json"),
        "api_keys": {},
    }


@router.post("", status_code=201, summary="Create and start a batch")
async def create_batch(
    body: BatchCreate, bg: BackgroundTasks, _: VerifiedToken
) -> dict[str, Any]:
    topics = [t.strip() for t in body.topics if t.strip()]
    if not topics:
        raise HTTPException(status_code=422, detail="No usable topics supplied")

    batch = batch_service.create(name=body.name, topics=topics, template=_template(body))
    bg.add_task(_run_safely, batch["id"])
    return batch


async def _run_safely(batch_id: str) -> None:
    try:
        await batch_service.run(batch_id)
    except Exception:  # already logged inside; never crash the worker
        pass


@router.get("", summary="List batches")
async def list_batches(limit: int = 50, offset: int = 0, _: VerifiedToken = None) -> dict:
    total, items = batch_service.list_batches(limit=limit, offset=offset)
    return {"total": total, "batches": items}


@router.get("/{batch_id}", summary="Batch detail with per-task status")
async def get_batch(batch_id: str, _: VerifiedToken) -> dict:
    detail = batch_service.detail(batch_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return detail


@router.delete("/{batch_id}", summary="Delete a batch (keeps its tasks)")
async def delete_batch(batch_id: str, _: VerifiedToken) -> dict:
    batch_service.delete(batch_id)
    return {"ok": True, "batch_id": batch_id}
