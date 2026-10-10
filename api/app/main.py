"""VidiForge FastAPI application entry."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.config import load_toml_overrides, settings
from app.db.database import init_db
from app.models.schema import HealthResponse
from app.router import api_router


logging.basicConfig(
    level=logging.INFO if settings.vidiforge_env == "production" else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("vidiforge")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("VidiForge starting (env=%s)", settings.vidiforge_env)
    load_toml_overrides()
    settings.storage_output_dir and os.makedirs(settings.outputs_path, exist_ok=True)
    os.makedirs(settings.cache_path, exist_ok=True)
    os.makedirs(settings.upload_path, exist_ok=True)
    init_db()
    log.info("Storage: outputs=%s cache=%s upload=%s",
             settings.outputs_path, settings.cache_path, settings.upload_path)
    log.info("FFmpeg: %s", settings.ffmpeg_path)
    yield
    log.info("VidiForge shutting down")


app = FastAPI(
    title="VidiForge · AI Video Studio",
    description="智選銀河 · 一鍵生成 AI 短視頻",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# === CORS ===
origins = [o.strip() for o in settings.web_origin.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", response_model=HealthResponse, tags=["meta"])
async def healthz() -> HealthResponse:
    return HealthResponse(
        ok=True,
        env=settings.vidiforge_env,
        ffmpeg=settings.ffmpeg_path,
    )


@app.get("/", tags=["meta"])
async def root() -> dict:
    return {
        "name": "VidiForge",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/healthz",
    }


app.include_router(api_router, prefix="/api/v1")