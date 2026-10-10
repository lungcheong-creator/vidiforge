"""Configuration loader for VidiForge API.

Reads from environment variables (with sensible defaults) and a `settings.toml`
file if present. Provider switches are exposed for the LLM/TTS/Material layers.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]
TOML_PATH = ROOT / "app" / "config" / "settings.toml"


class Settings(BaseSettings):
    """Application settings, populated from env vars + optional TOML."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # === Server ===
    vidiforge_env: Literal["development", "production"] = "development"
    host: str = "0.0.0.0"
    port: int = 8080

    # === Security ===
    vidiforge_api_token: str = Field(default="devtoken123", min_length=8)
    vidiforge_master_key: str = Field(default="")

    # === CORS ===
    web_origin: str = "http://localhost:3000"

    # === Storage ===
    storage_output_dir: str = "storage/outputs"
    storage_cache_dir: str = "storage/cache"
    storage_upload_dir: str = "storage/upload"
    database_url: str = "sqlite:///./storage/vidiforge.db"

    # === Provider switches ===
    llm_provider: Literal[
        "openai", "anthropic", "deepseek", "gemini", "moonshot",
        "qwen", "openai_compatible",
    ] = "openai"
    voice_provider: Literal["edge", "azure", "elevenlabs", "siliconflow"] = "edge"
    subtitle_provider: Literal["edge", "whisper"] = "edge"
    material_provider: Literal["pexels", "pixabay"] = "pexels"

    # === Server-side fallback API keys (BYOK via Settings takes precedence) ===
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    deepseek_api_key: str = ""
    gemini_api_key: str = ""
    moonshot_api_key: str = ""
    qwen_api_key: str = ""
    openai_compatible_api_key: str = ""
    openai_compatible_base_url: str = ""
    pexels_api_key: str = ""
    pixabay_api_key: str = ""
    elevenlabs_api_key: str = ""
    azure_speech_key: str = ""
    azure_speech_region: str = ""
    siliconflow_api_key: str = ""

    # === Whisper ===
    whisper_model_size: str = "large-v3"

    # === Helpers ===
    @property
    def storage_root(self) -> Path:
        return (ROOT / "storage").resolve()

    @property
    def outputs_path(self) -> Path:
        return (ROOT / self.storage_output_dir).resolve()

    @property
    def cache_path(self) -> Path:
        return (ROOT / self.storage_cache_dir).resolve()

    @property
    def upload_path(self) -> Path:
        return (ROOT / self.storage_upload_dir).resolve()

    @property
    def ffmpeg_path(self) -> str:
        """Resolve the FFmpeg binary path."""
        from app.utils.ffmpeg import get_ffmpeg_binary
        return get_ffmpeg_binary()


settings = Settings()  # type: ignore[call-arg]


def load_toml_overrides() -> None:
    """Optionally overlay values from settings.toml (non-secret UI toggles only)."""
    if not TOML_PATH.exists():
        return
    try:
        import tomllib  # py3.11+
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]
    with open(TOML_PATH, "rb") as f:
        data = tomllib.load(f)
    app_section = data.get("app", {})
    ui_section = data.get("ui", {})
    whisper_section = data.get("whisper", {})

    if "llm_provider" in app_section:
        settings.llm_provider = app_section["llm_provider"]
    if "voice_provider" in app_section:
        settings.voice_provider = app_section["voice_provider"]
    if "subtitle_provider" in app_section:
        settings.subtitle_provider = app_section["subtitle_provider"]
    if "material_provider" in app_section:
        settings.material_provider = app_section["material_provider"]

    if "model_size" in whisper_section:
        settings.whisper_model_size = whisper_section["model_size"]

    # UI section is exposed at /api/v1/settings/ui
    settings.__dict__["_ui_toml"] = ui_section