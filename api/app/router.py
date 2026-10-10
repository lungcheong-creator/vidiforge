"""Aggregate v1 routers."""

from fastapi import APIRouter

from app.controllers.v1 import audio, base, llm, material, settings as settings_ctrl, subtitle, video


api_router = APIRouter()
api_router.include_router(base.router, tags=["meta"])
api_router.include_router(video.router, prefix="/videos", tags=["videos"])
api_router.include_router(video.tasks_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(llm.router, prefix="/llm", tags=["llm"])
api_router.include_router(audio.router, prefix="/audio", tags=["audio"])
api_router.include_router(subtitle.router, prefix="/subtitle", tags=["subtitle"])
api_router.include_router(material.router, prefix="/materials", tags=["materials"])
api_router.include_router(settings_ctrl.router, prefix="/settings", tags=["settings"])