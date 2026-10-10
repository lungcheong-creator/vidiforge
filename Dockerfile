# VidiForge - one-image FastAPI + static frontend
# Used by `gcloud run deploy --source .` (no multi-stage; we pre-build locally)

FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    libsm6 libxext6 libxrender1 libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps
COPY api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY api/ ./

# Pre-built static frontend
COPY web/out ./static

# Storage
RUN mkdir -p /app/storage/outputs /app/storage/cache /app/storage/upload

# Non-root user
RUN useradd -m -u 1000 vidiforge && chown -R vidiforge:vidiforge /app
USER vidiforge

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8080/healthz || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
