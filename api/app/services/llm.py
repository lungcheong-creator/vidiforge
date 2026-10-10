"""LLM service — multi-provider script generation.

All providers speak either OpenAI-compatible Chat Completions (openai, deepseek,
moonshot, qwen, openai_compatible, gemini) or Anthropic Messages (anthropic).
The unified interface returns a `Script` (title + segments).
"""

from __future__ import annotations

import json
import re
from typing import Any

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config.config import settings
from app.models.const import LLMProvider
from app.models.exception import ConfigError, ProviderError
from app.models.schema import Script, ScriptSegment


_SYSTEM_PROMPT_ZH = """你是一名短視頻腳本撰寫專家。根據用戶的主題，輸出一段 30-90 秒的中文短視頻腳本。
要求：
- 開頭吸引人的鉤子（hook）
- 3-7 段短句，每段 5-10 字，便於配音
- 結尾一句總結或行動呼籲
- 為每段提供 1 個英文檢索關鍵詞（用於匹配素材）
嚴格按照以下 JSON 格式輸出，不要有其他文字：

{
  "title": "腳本標題",
  "segments": [
    {"text": "第一段文本", "keyword": "keyword1"},
    {"text": "第二段文本", "keyword": "keyword2"}
  ]
}"""

_SYSTEM_PROMPT_EN = """You are a short-video script writer. Given a topic, output a 30-90s video script.
Requirements:
- Compelling hook opening
- 3-7 short segments of 5-10 words each, suitable for TTS narration
- Closing line summarizing or with a call-to-action
- Each segment needs 1 keyword in English for stock footage matching

Return ONLY this JSON format, no other text:

{
  "title": "Script title",
  "segments": [
    {"text": "First segment text", "keyword": "keyword1"},
    {"text": "Second segment text", "keyword": "keyword2"}
  ]
}"""


def _resolve_system_prompt(language: str) -> str:
    return _SYSTEM_PROMPT_ZH if language.startswith("zh") else _SYSTEM_PROMPT_EN


def _resolve_key(provider: LLMProvider, byok: dict[str, str]) -> str:
    """Resolve an API key for the given provider, in priority order:
    1. byok dict (per-request override)
    2. server-side env var
    """
    byok_keys = {
        LLMProvider.OPENAI: "openai",
        LLMProvider.ANTHROPIC: "anthropic",
        LLMProvider.DEEPSEEK: "deepseek",
        LLMProvider.GEMINI: "gemini",
        LLMProvider.MOONSHOT: "moonshot",
        LLMProvider.QWEN: "qwen",
        LLMProvider.OPENAI_COMPATIBLE: "openai_compatible",
    }
    byok_name = byok_keys.get(provider, "")
    if byok_name and byok.get(byok_name):
        return byok[byok_name]

    env_map = {
        LLMProvider.OPENAI: settings.openai_api_key,
        LLMProvider.ANTHROPIC: settings.anthropic_api_key,
        LLMProvider.DEEPSEEK: settings.deepseek_api_key,
        LLMProvider.GEMINI: settings.gemini_api_key,
        LLMProvider.MOONSHOT: settings.moonshot_api_key,
        LLMProvider.QWEN: settings.qwen_api_key,
        LLMProvider.OPENAI_COMPATIBLE: settings.openai_compatible_api_key,
    }
    key = env_map.get(provider, "")
    if not key:
        raise ConfigError(
            f"No API key found for provider '{provider.value}'. "
            f"Set it in Settings or supply via request body."
        )
    return key


def _resolve_model(provider: LLMProvider, override: str | None = None) -> tuple[str, str | None]:
    """Return (model_name, base_url) for the provider, honouring an override."""
    defaults: dict[LLMProvider, tuple[str, str | None]] = {
        LLMProvider.OPENAI: ("gpt-4o-mini", None),
        LLMProvider.ANTHROPIC: ("claude-3-5-sonnet-20241022", None),
        LLMProvider.DEEPSEEK: ("deepseek-chat", "https://api.deepseek.com/v1"),
        LLMProvider.GEMINI: ("gemini-1.5-flash", None),
        LLMProvider.MOONSHOT: ("moonshot-v1-8k", "https://api.moonshot.cn/v1"),
        LLMProvider.QWEN: ("qwen-plus", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        LLMProvider.OPENAI_COMPATIBLE: (
            "gpt-4o-mini",
            settings.openai_compatible_base_url or None,
        ),
    }
    if provider not in defaults:
        raise ConfigError(f"Unknown LLM provider: {provider.value}")
    model, base_url = defaults[provider]
    return (override or model), base_url


async def list_models() -> list[dict[str, Any]]:
    """Curated model catalogue for the UI (provider → models)."""
    return [
        {"provider": "deepseek", "id": "deepseek-flash", "name": "DeepSeek V4.1 Flash",
         "note": "1M context · fast · recommended for batch"},
        {"provider": "deepseek", "id": "deepseek-v4-pro", "name": "DeepSeek V4 Pro",
         "note": "1M context · highest quality"},
        {"provider": "openai", "id": "gpt-4o-mini", "name": "GPT-4o mini", "note": ""},
        {"provider": "anthropic", "id": "claude-3-5-sonnet-20241022",
         "name": "Claude 3.5 Sonnet", "note": ""},
        {"provider": "gemini", "id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "note": ""},
        {"provider": "moonshot", "id": "moonshot-v1-8k", "name": "Moonshot Kimi", "note": ""},
        {"provider": "qwen", "id": "qwen-plus", "name": "通義千問 Plus", "note": ""},
    ]


def _strip_code_fence(text: str) -> str:
    """Strip ```json ... ``` fences if present."""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text


def _parse_script(raw: str, fallback_topic: str) -> Script:
    """Parse LLM JSON output into Script. Falls back to a minimal script if needed."""
    raw = _strip_code_fence(raw)
    try:
        data = json.loads(raw)
        segments_data = data.get("segments") or []
        segments = [
            ScriptSegment(
                id=i + 1,
                text=s.get("text", "").strip(),
                keyword=s.get("keyword", "").strip(),
                duration=5.0,
            )
            for i, s in enumerate(segments_data)
            if s.get("text")
        ]
        if not segments:
            raise ValueError("Empty segments")
        return Script(title=data.get("title", fallback_topic), segments=segments)
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        raise ProviderError(f"Failed to parse script from LLM: {e}\nRaw output: {raw[:500]}")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def generate_script(
    *,
    topic: str,
    keywords: list[str],
    provider: LLMProvider | None = None,
    model: str | None = None,
    language: str = "zh-CN",
    segment_count: int = 5,
    byok: dict[str, str] | None = None,
) -> Script:
    """Generate a Script object via the configured LLM provider."""
    provider = provider or LLMProvider(settings.llm_provider)
    byok = byok or {}

    api_key = _resolve_key(provider, byok)
    model_name, base_url = _resolve_model(provider, model)
    system_prompt = _resolve_system_prompt(language)

    user_msg = topic
    if keywords:
        user_msg += "\n關鍵詞：" + ", ".join(keywords)
    user_msg += f"\n請生成 {segment_count} 段。"

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    try:
        resp = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.8,
            max_tokens=1500,
        )
        raw = resp.choices[0].message.content or ""
    except Exception as e:
        raise ProviderError(f"LLM call failed: {e}") from e
    finally:
        await client.close()

    return _parse_script(raw, fallback_topic=topic)


async def list_providers() -> list[dict[str, Any]]:
    """Return the catalogue of LLM providers for the /llm/providers endpoint."""
    catalogue = [
        {"id": "openai", "name": "OpenAI", "default_model": "gpt-4o-mini", "env_key": "openai_api_key", "byok_key": "openai"},
        {"id": "anthropic", "name": "Anthropic Claude", "default_model": "claude-3-5-sonnet", "env_key": "anthropic_api_key", "byok_key": "anthropic"},
        {"id": "deepseek", "name": "DeepSeek", "default_model": "deepseek-chat", "env_key": "deepseek_api_key", "byok_key": "deepseek"},
        {"id": "gemini", "name": "Google Gemini", "default_model": "gemini-1.5-flash", "env_key": "gemini_api_key", "byok_key": "gemini"},
        {"id": "moonshot", "name": "Moonshot (Kimi)", "default_model": "moonshot-v1-8k", "env_key": "moonshot_api_key", "byok_key": "moonshot"},
        {"id": "qwen", "name": "通義千問", "default_model": "qwen-plus", "env_key": "qwen_api_key", "byok_key": "qwen"},
        {"id": "openai_compatible", "name": "OpenAI Compatible", "default_model": "custom", "env_key": "openai_compatible_api_key", "byok_key": "openai_compatible"},
    ]
    out = []
    for c in catalogue:
        env_val = getattr(settings, c["env_key"], "")
        out.append({
            **c,
            "available": bool(env_val),
            "active": settings.llm_provider == c["id"],
        })
    return out