"""Pydantic schemas for API requests and responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.const import (
    AspectRatio,
    Language,
    LLMProvider,
    MaterialProvider,
    SubtitleProvider,
    TaskStatus,
    VoiceProvider,
)


# === Script ===
class ScriptSegment(BaseModel):
    id: int
    text: str
    keyword: str = ""
    duration: float = 5.0  # seconds


class Script(BaseModel):
    title: str
    segments: list[ScriptSegment]


# === Voice ===
class VoiceConfig(BaseModel):
    provider: VoiceProvider = VoiceProvider.EDGE
    voice_id: str = "zh-CN-XiaoxiaoNeural"
    speed: float = 1.0
    pitch: float = 0.0


# === Subtitle ===
class SubtitleConfig(BaseModel):
    provider: SubtitleProvider = SubtitleProvider.EDGE
    font: str = "Noto Sans CJK SC"
    font_size: int = 48
    font_color: str = "#FFFFFF"
    position: str = "bottom"  # bottom | center | top
    outline_color: str = "#000000"
    outline_width: int = 2


# === Material ===
class MaterialConfig(BaseModel):
    provider: MaterialProvider = MaterialProvider.PEXELS
    orientation: str = "portrait"  # portrait | landscape | square


# === Background music ===
class BGMConfig(BaseModel):
    enabled: bool = True
    volume: float = 0.3
    random: bool = True
    path: Optional[str] = None  # explicit BGM file path


# === Video generation request ===
class VideoRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500)
    keywords: list[str] = Field(default_factory=list)
    language: Language = Language.ZH
    aspect: AspectRatio = AspectRatio.VERTICAL
    duration: int = Field(default=30, ge=5, le=180)
    segments: int = Field(default=5, ge=1, le=20)

    llm_provider: LLMProvider = LLMProvider.OPENAI
    script: Optional[Script] = None  # user-provided script override

    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    subtitle: SubtitleConfig = Field(default_factory=SubtitleConfig)
    material: MaterialConfig = Field(default_factory=MaterialConfig)
    bgm: BGMConfig = Field(default_factory=BGMConfig)

    # Optional overrides (BYOK)
    api_keys: dict[str, str] = Field(default_factory=dict)


# === Task responses ===
class TaskStage(BaseModel):
    name: str  # "script" | "voice" | "footage" | "subtitle" | "bgm" | "render"
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None


class VideoTask(BaseModel):
    id: str
    topic: str
    aspect: AspectRatio
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    current_stage: Optional[str] = None
    script: Optional[Script] = None
    output_path: Optional[str] = None
    output_url: Optional[str] = None
    duration: Optional[float] = None
    file_size: Optional[int] = None
    stages: list[TaskStage] = Field(default_factory=list)
    error: Optional[str] = None
    config: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    total: int
    tasks: list[VideoTask]


# === Subtitle / Audio / Material sub-endpoints ===
class SubtitleRequest(BaseModel):
    script: Script
    voice_paths: list[str]
    config: SubtitleConfig = Field(default_factory=SubtitleConfig)


class AudioRequest(BaseModel):
    segments: list[ScriptSegment]
    config: VoiceConfig = Field(default_factory=VoiceConfig)


class MaterialUploadResponse(BaseModel):
    asset_id: str
    path: str
    url: str
    filename: str
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None


# === Settings / API Keys ===
class ApiKeyEntry(BaseModel):
    """Masked representation returned by GET."""
    provider: str
    masked: str
    updated_at: datetime
    has_value: bool


class ApiKeySave(BaseModel):
    provider: str
    value: str = Field(..., min_length=1)


class ApiKeyBulkSave(BaseModel):
    keys: dict[str, str]


# === Providers discovery ===
class LLMProviderInfo(BaseModel):
    id: LLMProvider
    name: str
    default_model: str
    requires_key: bool
    available: bool


class VoiceProviderInfo(BaseModel):
    id: VoiceProvider
    name: str
    voices: list[dict[str, Any]]
    requires_key: bool
    available: bool


class HealthResponse(BaseModel):
    ok: bool
    version: str = "0.1.0"
    env: str
    ffmpeg: str