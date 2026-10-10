"""Video generation endpoints — POST /videos, GET /tasks."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.middleware.verify_token import VerifiedToken
from app.models.schema import (
    TaskListResponse,
    VideoRequest,
    VideoTask,
)
from app.services import task as task_service


router = APIRouter()


@router.post("", response_model=VideoTask, status_code=201, summary="Generate a new short video")
async def create_video(
    request: VideoRequest,
    bg: BackgroundTasks,
    _: VerifiedToken,
) -> VideoTask:
    """Validate the request, persist a pending task, schedule the pipeline."""
    task = await task_service.create_task(request)
    # Schedule the pipeline to run in the background
    bg.add_task(_run_pipeline_safely, task.id, request)
    return task


async def _run_pipeline_safely(task_id: str, request: VideoRequest) -> None:
    """Wrap the pipeline so background exceptions don't crash the worker."""
    import logging
    log = logging.getLogger("vidiforge.pipeline")
    try:
        await task_service.run_pipeline(task_id, request)
    except Exception as e:
        log.exception("Pipeline failed for task %s", task_id, exc_info=e)


# ---- Task sub-router ----
tasks_router = APIRouter()


@tasks_router.get("", response_model=TaskListResponse, summary="List all tasks")
async def list_tasks(
    limit: int = 50,
    offset: int = 0,
    _: VerifiedToken = None,
) -> TaskListResponse:
    total, tasks = await task_service.list_tasks(limit=limit, offset=offset)
    return TaskListResponse(total=total, tasks=tasks)


@tasks_router.get("/{task_id}", response_model=VideoTask, summary="Get task status")
async def get_task(task_id: str, _: VerifiedToken) -> VideoTask:
    try:
        return await task_service.get_task(task_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@tasks_router.delete("/{task_id}", summary="Delete a task and its outputs")
async def delete_task(task_id: str, _: VerifiedToken) -> dict:
    await task_service.delete_task(task_id)
    return {"ok": True, "task_id": task_id}


@tasks_router.get("/{task_id}/file", summary="Resolve the rendered video for a task")
async def task_file(task_id: str, _: VerifiedToken):
    """Redirect to a signed GCS URL, or stream the object when signing is unavailable."""
    from fastapi.responses import RedirectResponse, StreamingResponse
    import io

    from app.config.config import settings
    from app.services import blobstore, tasks_repo

    raw = tasks_repo.get(task_id)
    if raw is None:
        raise HTTPException(status_code=404, detail="Task not found")
    key = raw.get("output_path")
    if not key:
        raise HTTPException(status_code=409, detail="Task has no output yet")

    if blobstore.enabled():
        url = blobstore.signed_url(key, minutes=settings.gcs_signed_url_minutes)
        if url:
            return RedirectResponse(url, status_code=302)
        data = blobstore.get_bytes(key)
        if data is None:
            raise HTTPException(status_code=404, detail="Output object missing")
        return StreamingResponse(io.BytesIO(data), media_type="video/mp4")

    raise HTTPException(status_code=404, detail="Output not found")