"""In-memory task state with optional Redis-ready interface.

This is the single source of truth for the live status of a running task.
Background tasks update it; HTTP handlers read it.
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Any, Optional

from sqlmodel import Session

from app.config.config import settings
from app.db.database import session_scope
from app.db.models import Task
from app.models.const import TaskStatus


class TaskState:
    """Wraps a Task row plus any in-flight progress data not yet persisted."""

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        self._lock = threading.Lock()
        self._live: dict[str, Any] = {}

    # ----- Persistence helpers -----
    def _load(self) -> Optional[Task]:
        with session_scope() as s:
            return s.get(Task, self.task_id)

    def _save(self, **fields: Any) -> None:
        fields["updated_at"] = datetime.utcnow()
        with session_scope() as s:
            task = s.get(Task, self.task_id)
            if not task:
                return
            for k, v in fields.items():
                setattr(task, k, v)
            s.add(task)
            s.commit()

    # ----- Public API -----
    def update(
        self,
        *,
        status: Optional[TaskStatus] = None,
        progress: Optional[int] = None,
        current_stage: Optional[str] = None,
        script_json: Optional[str] = None,
        output_path: Optional[str] = None,
        duration: Optional[float] = None,
        file_size: Optional[int] = None,
        error: Optional[str] = None,
    ) -> None:
        with self._lock:
            payload: dict[str, Any] = {}
            if status is not None:
                payload["status"] = status.value
            if progress is not None:
                payload["progress"] = max(0, min(100, progress))
            if current_stage is not None:
                payload["current_stage"] = current_stage
            if script_json is not None:
                payload["script_json"] = script_json
            if output_path is not None:
                payload["output_path"] = output_path
            if duration is not None:
                payload["duration"] = duration
            if file_size is not None:
                payload["file_size"] = file_size
            if error is not None:
                payload["error"] = error
            if payload:
                self._save(**payload)

    def get(self) -> Optional[Task]:
        return self._load()

    def to_dict(self) -> Optional[dict[str, Any]]:
        task = self._load()
        if not task:
            return None
        return {
            "id": task.id,
            "topic": task.topic,
            "aspect": task.aspect,
            "status": task.status,
            "progress": task.progress,
            "current_stage": task.current_stage,
            "script_json": task.script_json,
            "output_path": task.output_path,
            "duration": task.duration,
            "file_size": task.file_size,
            "error": task.error,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }