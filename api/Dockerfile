FROM python:3.11-slim

# Install system deps + FFmpeg + CJK fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    fonts-noto-color-emoji \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Storage directories (mounted as volume on Railway)
RUN mkdir -p /app/storage/outputs /app/storage/cache /app/storage/upload

# Non-root user for runtime
RUN useradd -m -u 1000 vidiforge && chown -R vidiforge:vidiforge /app
USER vidiforge

EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8080/healthz || exit 1

# Default command (Railway injects $PORT)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]