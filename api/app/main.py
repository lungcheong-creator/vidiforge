"""VidiForge FastAPI application entry.

Serves:
  - /api/v1/*      → JSON API (LLM, video, settings, etc.)
  - /*             → Static Next.js export (SPA frontend)

The frontend is built into ./static/ at image build time (see Dockerfile).
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config.config import load_toml_overrides, settings
from app.db.database import init_db
from app.models.schema import HealthResponse
from app.router import api_router


logging.basicConfig(
    level=logging.INFO if settings.vidiforge_env == "production" else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("vidiforge")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("VidiForge starting (env=%s)", settings.vidiforge_env)
    load_toml_overrides()
    # Cloud Run uses /tmp for writable storage; ensure it exists
    import os
    os.makedirs("/tmp/storage/outputs", exist_ok=True)
    os.makedirs("/tmp/storage/cache", exist_ok=True)
    os.makedirs("/tmp/storage/upload", exist_ok=True)
    # Symlink /app/storage -> /tmp/storage so the app's relative paths work
    if not os.path.exists("/app/storage"):
        try:
            os.symlink("/tmp/storage", "/app/storage", target_is_directory=True)
        except FileExistsError:
            pass
    # Also set DATABASE_URL to /tmp for persistence across requests
    if settings.database_url.startswith("sqlite:///./"):
        rel = settings.database_url.replace("sqlite:///./", "")
        os.environ["VIDIFORGE_DB_PATH"] = f"/tmp/storage/{rel}"
    settings.storage_output_dir and os.makedirs(settings.outputs_path, exist_ok=True)
    os.makedirs(settings.cache_path, exist_ok=True)
    os.makedirs(settings.upload_path, exist_ok=True)
    init_db()
    log.info("Storage: outputs=%s cache=%s upload=%s",
             settings.outputs_path, settings.cache_path, settings.upload_path)
    log.info("FFmpeg: %s", settings.ffmpeg_path)
    log.info("Static frontend: %s (exists=%s)", STATIC_DIR, STATIC_DIR.exists())
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

# === CORS (still useful for local dev with separate ports) ===
origins = [o.strip() for o in settings.web_origin.split(",") if o.strip() and o.strip() != "*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["meta"])
@app.get("/healthz", response_model=HealthResponse, tags=["meta"], include_in_schema=False)
async def healthz() -> HealthResponse:
    return HealthResponse(
        ok=True,
        env=settings.vidiforge_env,
        ffmpeg=settings.ffmpeg_path,
    )


@app.get("/api/health", response_model=HealthResponse, tags=["meta"])
async def api_health() -> HealthResponse:
    """Health endpoint under /api/ to bypass the SPA catch-all."""
    return HealthResponse(
        ok=True,
        env=settings.vidiforge_env,
        ffmpeg=settings.ffmpeg_path,
    )


@app.get("/api", tags=["meta"])
async def root() -> dict:
    return {
        "name": "VidiForge",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/healthz",
        "ui": "/" if STATIC_DIR.exists() else None,
    }


# Mount API under /api/v1
app.include_router(api_router, prefix="/api/v1")

# === Static frontend (SPA) ===
# If web/out/ exists (built into ./static/ by Dockerfile), mount it.
# Fallback: serve index.html for client-side routing.
if STATIC_DIR.exists():
    # Serve /_next/*, /assets/*, etc. as static files
    app.mount(
        "/_next",
        StaticFiles(directory=str(STATIC_DIR / "_next")),
        name="next-static",
    )

    @app.get("/", include_in_schema=False)
    async def serve_root():
        return FileResponse(str(STATIC_DIR / "index.html"), media_type="text/html")

    @app.get("/{path:path}", include_in_schema=False)
    async def serve_spa(path: str):
        # Don't intercept API or health endpoints — they have their own routes
        # mounted earlier, but the order may be such that this catch-all matches first.
        # So explicitly return 404 for any reserved prefix.
        if path.startswith("api/") or path.startswith("docs") or path.startswith("redoc") or path in ("healthz", "health") or path.startswith("openapi"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not Found")
        # Try to serve the actual static file first
        file_path = STATIC_DIR / path
        if file_path.is_file():
            return FileResponse(str(file_path))
        # Fallback to index.html for client-side routing
        return FileResponse(str(STATIC_DIR / "index.html"), media_type="text/html")
else:
    log.warning("Static frontend not found at %s — running API-only mode", STATIC_DIR)

    @app.get("/", tags=["meta"])
    async def root_api_only() -> dict:
        return {
            "name": "VidiForge",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/healthz",
            "note": "API-only mode. Static frontend not built.",
        }