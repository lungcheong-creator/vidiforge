"""Batch task runner.

A batch is a named list of topics run through the same pipeline
configuration. Tasks run sequentially so a batch never starves interactive
requests, and every task keeps its own row in `tasks/` so individual progress
is still visible.

NOTE (Cloud Run): background work only advances while the instance has CPU.
Deploy with `--no-cpu-throttling` (CPU always allocated) for batches to run
without a client polling. `--max-instances=1` also avoids two instances
picking up the same batch.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.models.schema import VideoRequest
from app.services import blobstore, task as task_service, tasks_repo


log = logging.getLogger("vidiforge.batch")

BATCH_PREFIX = "batches/"

# Only one batch advances at a time per instance.
_run_lock = asyncio.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _key(batch_id: str) -> str:
    return f"{BATCH_PREFIX}{batch_id}/batch.json"


def create(
    *,
    name: str,
    topics: list[str],
    template: dict[str, Any],
) -> dict[str, Any]:
    batch_id = uuid.uuid4().hex
    now = _now()
    batch = {
        "id": batch_id,
        "name": name,
        "status": "pending",
        "total": len(topics),
        "completed": 0,
        "failed": 0,
        "topics": topics,
        "task_ids": [],
        "template": template,
        "error": None,
        "created_at": now,
        "updated_at": now,
    }
    blobstore.put_json(_key(batch_id), batch)
    return batch


def get(batch_id: str) -> dict[str, Any] | None:
    return blobstore.get_json(_key(batch_id))


def update(batch_id: str, **fields: Any) -> dict[str, Any] | None:
    batch = get(batch_id)
    if batch is None:
        return None
    batch.update(fields)
    batch["updated_at"] = _now()
    blobstore.put_json(_key(batch_id), batch)
    return batch


def delete(batch_id: str) -> None:
    blobstore.delete_prefix(f"{BATCH_PREFIX}{batch_id}/")


def list_batches(limit: int = 50, offset: int = 0) -> tuple[int, list[dict[str, Any]]]:
    keys = blobstore.list_keys(BATCH_PREFIX, suffix="/batch.json")
    total = len(keys)
    keys = sorted(keys, reverse=True)[offset : offset + limit]
    batches = [b for b in (blobstore.get_json(k) for k in keys) if b]
    batches.sort(key=lambda b: b.get("created_at", ""), reverse=True)
    return total, batches


async def run(batch_id: str) -> None:
    """Run every topic in the batch, one task at a time."""
    async with _run_lock:
        batch = get(batch_id)
        if batch is None:
            log.warning("batch %s not found", batch_id)
            return

        update(batch_id, status="running")
        template = batch.get("template") or {}
        task_ids: list[str] = list(batch.get("task_ids") or [])
        completed = int(batch.get("completed") or 0)
        failed = int(batch.get("failed") or 0)

        for index, topic in enumerate(batch.get("topics") or []):
            # Skip topics already handled (idempotent restart).
            if index < len(task_ids):
                continue
            try:
                payload = dict(template)
                payload["topic"] = topic
                request = VideoRequest.model_validate(payload)

                created = await task_service.create_task(request)
                task_ids.append(created.id)
                update(batch_id, task_ids=task_ids)

                await task_service.run_pipeline(created.id, request)
                completed += 1
            except Exception as e:
                log.exception("batch %s topic %r failed", batch_id, topic)
                failed += 1
            finally:
                update(batch_id, completed=completed, failed=failed)

        update(
            batch_id,
            status="done" if failed == 0 else "failed",
            task_ids=task_ids,
            completed=completed,
            failed=failed,
        )
        log.info("batch %s finished: %s ok, %s failed", batch_id, completed, failed)


def detail(batch_id: str) -> dict[str, Any] | None:
    """Batch plus the current status of each of its tasks."""
    batch = get(batch_id)
    if batch is None:
        return None
    tasks = []
    for tid in batch.get("task_ids") or []:
        raw = tasks_repo.get(tid)
        if raw:
            tasks.append(
                {
                    "id": raw["id"],
                    "topic": raw.get("topic"),
                    "status": raw.get("status"),
                    "progress": raw.get("progress", 0),
                    "current_stage": raw.get("current_stage"),
                    "error": raw.get("error"),
                    "duration": raw.get("duration"),
                }
            )
    batch = dict(batch)
    batch["tasks"] = tasks
    return batch
