"""SQLModel ORM models for tasks, projects, API keys, and assets."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Task(SQLModel, table=True):
    __tablename__ = "task"

    id: str = Field(primary_key=True, index=True)
    project_id: Optional[str] = Field(default=None, index=True)
    topic: str
    aspect: str = "9:16"
    status: str = "pending"  # pending|running|done|failed
    progress: int = 0  # 0-100
    current_stage: Optional[str] = None
    script_json: Optional[str] = None
    output_path: Optional[str] = None
    duration: Optional[float] = None
    file_size: Optional[int] = None
    config_json: str  # full request snapshot
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class ApiKey(SQLModel, table=True):
    __tablename__ = "apikey"

    provider: str = Field(primary_key=True)
    ciphertext: bytes
    updated_at: datetime = Field(default_factory=_utcnow)


class Project(SQLModel, table=True):
    __tablename__ = "project"

    id: str = Field(primary_key=True, index=True)
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=_utcnow)


class Asset(SQLModel, table=True):
    __tablename__ = "asset"

    id: str = Field(primary_key=True, index=True)
    project_id: Optional[str] = Field(default=None, index=True)
    kind: str  # "video" | "image" | "audio"
    path: str
    meta_json: str = "{}"
    created_at: datetime = Field(default_factory=_utcnow)