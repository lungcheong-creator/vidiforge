"""Agent endpoints — conversational control of the pipeline."""

from __future__ import annotations

import logging
from typing import Any, Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from app.middleware.verify_token import VerifiedToken
from app.models.schema import VideoRequest
from app.services import agent as agent_service
from app.services import task as task_service


log = logging.getLogger("vidiforge.agent.api")
router = APIRouter()


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1)
    model: str = "deepseek-flash"


@router.post("/chat", summary="One agent turn (may create videos or inspect tasks)")
async def chat(body: ChatRequest, bg: BackgroundTasks, _: VerifiedToken) -> dict[str, Any]:
    # `schedule` hands the pipeline to FastAPI's background runner so the HTTP
    # response returns immediately with the task id.
    def schedule(task_id: str, request: VideoRequest) -> None:
        bg.add_task(_run_pipeline, task_id, request)

    try:
        return await agent_service.chat(
            messages=[m.model_dump() for m in body.messages],
            model=body.model,
            schedule=schedule,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


async def _run_pipeline(task_id: str, request: VideoRequest) -> None:
    try:
        await task_service.run_pipeline(task_id, request)
    except Exception:
        log.exception("agent-triggered pipeline failed for %s", task_id)


@router.get("/tools", summary="List the tools the agent can call")
async def list_tools(_: VerifiedToken) -> list[dict[str, Any]]:
    return [
        {"name": t["function"]["name"], "description": t["function"]["description"]}
        for t in agent_service.TOOLS
    ]
