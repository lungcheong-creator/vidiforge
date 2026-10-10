"""Agent service — conversational control of the pipeline via tool calls.

Uses the configured LLM's OpenAI-compatible function-calling interface. The
model can create videos, inspect task status and list recent work; the loop is
bounded so a confused model cannot spin forever.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Awaitable, Callable

from openai import AsyncOpenAI

from app.config.config import settings
from app.models.const import LLMProvider
from app.models.exception import ConfigError, ProviderError
from app.models.schema import (
    AspectRatio,
    BGMConfig,
    Language,
    MaterialConfig,
    SubtitleConfig,
    VideoRequest,
    VoiceConfig,
)
from app.services import llm as llm_service
from app.services import tasks_repo


log = logging.getLogger("vidiforge.agent")

MAX_STEPS = 5

SYSTEM_PROMPT = """你是 VidiForge 的創作助手，負責把使用者的想法變成短影片任務。

你可以使用工具：
- create_video：建立一支新的短影片（會自動生成腳本、配音、素材、字幕）
- list_tasks：列出最近的任務
- get_task：查詢某個任務的進度
- suggest_keywords：為主題建議英文素材檢索關鍵詞

規則：
- 使用者描述想法時，先確認主題，然後直接呼叫 create_video，不要只是說明你會做什麼。
- 只有在資訊不足（例如完全沒提到主題）時才反問。
- 回覆使用繁體中文，簡潔，不要客套。
- 建立任務後，告訴使用者任務編號與預估時間（約 2 分鐘）。"""

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "create_video",
            "description": "建立一支新的短影片任務。會自動生成腳本、配音、素材、字幕並渲染。",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "影片主題，用中文描述"},
                    "aspect": {
                        "type": "string",
                        "enum": ["9:16", "16:9", "1:1"],
                        "description": "畫幅，預設 9:16 直式",
                    },
                    "duration": {"type": "integer", "description": "秒數，預設 30"},
                    "segments": {"type": "integer", "description": "腳本段數，預設 5"},
                    "voice_id": {
                        "type": "string",
                        "description": "Edge TTS 音色，例如 zh-CN-XiaoxiaoNeural",
                    },
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "列出最近的影片任務與其狀態",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "回傳筆數，預設 10"}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_task",
            "description": "查詢單一任務的進度",
            "parameters": {
                "type": "object",
                "properties": {"task_id": {"type": "string"}},
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_keywords",
            "description": "為一個主題建議英文素材檢索關鍵詞",
            "parameters": {
                "type": "object",
                "properties": {"topic": {"type": "string"}},
                "required": ["topic"],
            },
        },
    },
]


def _build_request(args: dict[str, Any]) -> VideoRequest:
    return VideoRequest(
        topic=str(args.get("topic", "")).strip() or "未命名主題",
        keywords=[],
        language=Language.ZH,
        aspect=AspectRatio(args.get("aspect") or "9:16"),
        duration=int(args.get("duration") or 30),
        segments=int(args.get("segments") or 5),
        llm_provider=LLMProvider.DEEPSEEK,
        llm_model="deepseek-flash",
        script=None,
        voice=VoiceConfig(voice_id=args.get("voice_id") or "zh-CN-XiaoxiaoNeural"),
        subtitle=SubtitleConfig(),
        material=MaterialConfig(),
        bgm=BGMConfig(enabled=True, volume=0.3, random=True, path=None),
        api_keys={},
    )


async def _exec_create_video(args: dict[str, Any], schedule: Callable[[str, VideoRequest], None]) -> dict:
    from app.services import task as task_service

    request = _build_request(args)
    created = await task_service.create_task(request)
    schedule(created.id, request)
    return {
        "task_id": created.id,
        "topic": created.topic,
        "aspect": created.aspect,
        "status": "queued",
    }


def _exec_list_tasks(args: dict[str, Any]) -> dict:
    limit = int(args.get("limit") or 10)
    _, tasks = tasks_repo.list_tasks(limit=limit, offset=0)
    return {
        "count": len(tasks),
        "tasks": [
            {
                "id": t.get("id"),
                "topic": t.get("topic"),
                "status": t.get("status"),
                "progress": t.get("progress", 0),
            }
            for t in tasks
        ],
    }


def _exec_get_task(args: dict[str, Any]) -> dict:
    task = tasks_repo.get(str(args.get("task_id", "")))
    if task is None:
        return {"error": "task not found"}
    return {
        "id": task.get("id"),
        "topic": task.get("topic"),
        "status": task.get("status"),
        "progress": task.get("progress", 0),
        "current_stage": task.get("current_stage"),
        "error": task.get("error"),
        "duration": task.get("duration"),
    }


def _exec_suggest_keywords(args: dict[str, Any]) -> dict:
    topic = str(args.get("topic", "")).strip()
    # Deterministic, dependency-free suggestion — the model can refine these.
    return {
        "topic": topic,
        "keywords": [
            f"{topic} interior",
            f"{topic} lifestyle",
            f"{topic} closeup",
            f"{topic} morning light",
            f"{topic} minimal",
        ],
    }


async def chat(
    *,
    messages: list[dict[str, Any]],
    model: str | None = None,
    provider: LLMProvider | None = None,
    byok: dict[str, str] | None = None,
    schedule: Callable[[str, VideoRequest], None] | None = None,
) -> dict[str, Any]:
    """Run one agent turn (possibly several tool rounds)."""
    provider = provider or LLMProvider.DEEPSEEK
    byok = byok or {}
    api_key = llm_service._resolve_key(provider, byok)  # noqa: SLF001 - shared helper
    model_name, base_url = llm_service._resolve_model(provider, model or "deepseek-flash")  # noqa: SLF001

    convo: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}, *messages]
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    tool_log: list[dict[str, Any]] = []

    try:
        for _ in range(MAX_STEPS):
            try:
                resp = await client.chat.completions.create(
                    model=model_name,
                    messages=convo,
                    tools=TOOLS,
                    temperature=0.6,
                    max_tokens=1200,
                )
            except Exception as e:
                raise ProviderError(f"Agent LLM call failed: {e}") from e

            msg = resp.choices[0].message
            calls = msg.tool_calls or []

            if not calls:
                return {
                    "reply": msg.content or "",
                    "model": model_name,
                    "tool_calls": tool_log,
                }

            # Echo the assistant turn (with its tool_calls) back into the history.
            convo.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": c.id,
                            "type": "function",
                            "function": {"name": c.function.name, "arguments": c.function.arguments},
                        }
                        for c in calls
                    ],
                }
            )

            for call in calls:
                name = call.function.name
                try:
                    args = json.loads(call.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}

                try:
                    if name == "create_video":
                        if schedule is None:
                            result: Any = {"error": "video creation unavailable"}
                        else:
                            result = await _exec_create_video(args, schedule)
                    elif name == "list_tasks":
                        result = _exec_list_tasks(args)
                    elif name == "get_task":
                        result = _exec_get_task(args)
                    elif name == "suggest_keywords":
                        result = _exec_suggest_keywords(args)
                    else:
                        result = {"error": f"unknown tool {name}"}
                except Exception as e:  # tool failures should not kill the turn
                    log.exception("tool %s failed", name)
                    result = {"error": str(e)}

                tool_log.append({"tool": name, "arguments": args, "result": result})
                convo.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

        return {
            "reply": "（已達工具呼叫上限，請再試一次或把需求說得更具體。）",
            "model": model_name,
            "tool_calls": tool_log,
        }
    finally:
        await client.close()
