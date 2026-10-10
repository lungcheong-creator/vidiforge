"""Task persistence.

Backed by the blob store (GCS in production, local files under storage/ in
development), so state survives instance restarts and is consistent across
every Cloud Run instance. SQLite is intentionally not used for tasks for that
reason.
"""

from __future__ import annotations

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Iterable

from app.services import blobstore

log = logging.getLogger("vidiforge.tasks_repo")

TASK_PREFIX = "tasks/"
_MAX_LIST = 200


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _task_key(task_id: str) -> str:
    return f"{TASK_PREFIX}{task_id}/task.json"


def create(
    *,
    topic: str,
    aspect: str,
    config: dict[str, Any],
    task_id: str | None = None,
) -> dict[str, Any]:
    task_id = task_id or uuid.uuid4().hex
    now = _now()
    task = {
        "id": task_id,
        "topic": topic,
        "aspect": aspect,
        "status": "pending",
        "progress": 0,
        "current_stage": None,
        "script": None,
        "output_path": None,
        "output_url": None,
        "duration": None,
        "file_size": None,
        "error": None,
        "config": config,
        "created_at": now,
        "updated_at": now,
    }
    blobstore.put_json(_task_key(task_id), task)
    return task


def get(task_id: str) -> dict[str, Any] | None:
    return blobstore.get_json(_task_key(task_id))


def update(task_id: str, **fields: Any) -> dict[str, Any] | None:
    task = get(task_id)
    if task is None:
        return None
    task.update(fields)
    task["updated_at"] = _now()
    blobstore.put_json(_task_key(task_id), task)
    return task


def delete(task_id: str) -> None:
    blobstore.delete_prefix(f"{TASK_PREFIX}{task_id}/")


def list_tasks(limit: int = 50, offset: int = 0) -> tuple[int, list[dict[str, Any]]]:
    keys = blobstore.list_keys(TASK_PREFIX, suffix="/task.json")
    total = len(keys)

    # Newest first, using the parent directory name as a cheap sort key.
    keys = sorted(keys, reverse=True)[offset : offset + limit]

    tasks: list[dict[str, Any]] = []
    if keys:
        # Reading many objects sequentially would dominate the request time.
        with ThreadPoolExecutor(max_workers=min(16, len(keys))) as pool:
            for task in pool.map(blobstore.get_json, keys):
                if task:
                    tasks.append(task)
    tasks.sort(key=lambda t: t.get("created_at", ""), reverse=True)
    return total, tasks


def output_key(task_id: str, filename: str) -> str:
    return f"{TASK_PREFIX}{task_id}/{filename}"
