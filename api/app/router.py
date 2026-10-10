"""Aggregate v1 routers."""

from fastapi import APIRouter

from app.controllers.v1 import (
    agent,
    audio,
    base,
    batch,
    files,
    llm,
    material,
    settings as settings_ctrl,
    subtitle,
    video,
)


api_router = APIRouter()

# Meta
api_router.include_router(base.router, tags=["meta"])

# Core resources
api_router.include_router(video.router, prefix="/videos", tags=["videos"])
api_router.include_router(video.tasks_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(llm.router, prefix="/llm", tags=["llm"])
api_router.include_router(audio.router, prefix="/audio", tags=["audio"])
api_router.include_router(subtitle.router, prefix="/subtitle", tags=["subtitle"])
api_router.include_router(material.router, prefix="/materials", tags=["materials"])
api_router.include_router(batch.router, prefix="/batches", tags=["batches"])
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
api_router.include_router(settings_ctrl.router, prefix="/settings", tags=["settings"])

# Media serving lives at the API root so output paths stay short and stable
api_router.include_router(files.router, tags=["files"])
