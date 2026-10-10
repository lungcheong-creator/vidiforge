"""Live task state.

Thin wrapper over `tasks_repo` so the pipeline can report progress without
knowing how tasks are persisted.
"""

from __future__ import annotations

from typing import Any

from app.models.const import TaskStatus
from app.services import tasks_repo


class TaskState:
    def __init__(self, task_id: str) -> None:
        self.task_id = task_id

    def update(
        self,
        *,
        status: TaskStatus | None = None,
        progress: int | None = None,
        current_stage: str | None = None,
        script: dict[str, Any] | None = None,
        output_key: str | None = None,
        duration: float | None = None,
        file_size: int | None = None,
        error: str | None = None,
        clear_stage: bool = False,
    ) -> None:
        fields: dict[str, Any] = {}
        if status is not None:
            fields["status"] = status.value
        if progress is not None:
            fields["progress"] = max(0, min(100, int(progress)))
        if current_stage is not None:
            fields["current_stage"] = current_stage
        if clear_stage:
            fields["current_stage"] = None
        if script is not None:
            fields["script"] = script
        if output_key is not None:
            fields["output_path"] = output_key
        if duration is not None:
            fields["duration"] = duration
        if file_size is not None:
            fields["file_size"] = file_size
        if error is not None:
            fields["error"] = error
        if fields:
            tasks_repo.update(self.task_id, **fields)

    def get(self) -> dict[str, Any] | None:
        return tasks_repo.get(self.task_id)
