"""Text-to-speech service. Default provider: edge-tts (free, no key required).
Other providers: Azure Speech, ElevenLabs, SiliconFlow.
"""

from __future__ import annotations

import asyncio
import io
import os
import uuid
from pathlib import Path
from typing import Any

import edge_tts
import httpx

from app.config.config import settings
from app.models.const import EDGE_VOICES, VoiceProvider
from app.models.exception import ConfigError, ProviderError
from app.models.schema import ScriptSegment, VoiceConfig


async def synthesize_edge(text: str, voice_id: str, speed: float, pitch: float, output_path: Path) -> None:
    """Generate TTS via edge-tts (no API key required)."""
    rate = f"{int((speed - 1.0) * 100):+d}%"
    pitch_str = f"{int(pitch * 100):+d}Hz"
    communicate = edge_tts.Communicate(text=text, voice=voice_id, rate=rate, pitch=pitch_str)
    await communicate.save(str(output_path))


async def synthesize_azure(text: str, voice_id: str, output_path: Path) -> None:
    """Use Azure Speech SDK via REST API."""
    if not settings.azure_speech_key or not settings.azure_speech_region:
        raise ConfigError("Azure Speech key/region not configured.")
    region = settings.azure_speech_region
    url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    ssml = f"""
    <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-CN'>
      <voice name='{voice_id}'><prosody rate='0%'>{text}</prosody></voice>
    </speak>
    """.strip()
    headers = {
        "Ocp-Apim-Subscription-Key": settings.azure_speech_key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, content=ssml, headers=headers)
    if r.status_code != 200:
        raise ProviderError(f"Azure TTS error {r.status_code}: {r.text[:200]}")
    output_path.write_bytes(r.content)


async def synthesize_elevenlabs(text: str, voice_id: str, output_path: Path) -> None:
    if not settings.elevenlabs_api_key:
        raise ConfigError("ElevenLabs API key not configured.")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": settings.elevenlabs_api_key, "Accept": "audio/mpeg"}
    payload = {"text": text, "model_id": "eleven_multilingual_v2"}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, json=payload, headers=headers)
    if r.status_code != 200:
        raise ProviderError(f"ElevenLabs error {r.status_code}: {r.text[:200]}")
    output_path.write_bytes(r.content)


async def synthesize_siliconflow(text: str, voice_id: str, output_path: Path) -> None:
    if not settings.siliconflow_api_key:
        raise ConfigError("SiliconFlow API key not configured.")
    url = "https://api.siliconflow.cn/v1/audio/speech"
    headers = {"Authorization": f"Bearer {settings.siliconflow_api_key}"}
    payload = {"model": "FunAudioLLM/CosyVoice2-0.5B", "input": text, "voice": voice_id}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, json=payload, headers=headers)
    if r.status_code != 200:
        raise ProviderError(f"SiliconFlow error {r.status_code}: {r.text[:200]}")
    output_path.write_bytes(r.content)


async def synthesize_segment(
    segment: ScriptSegment,
    config: VoiceConfig,
    output_dir: Path,
) -> Path:
    """Synthesize one segment and return its file path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"seg_{segment.id:03d}_{uuid.uuid4().hex[:8]}.mp3"

    if config.voice_provider == VoiceProvider.EDGE:
        await synthesize_edge(segment.text, config.voice_id, config.speed, config.pitch, output_path)
    elif config.voice_provider == VoiceProvider.AZURE:
        await synthesize_azure(segment.text, config.voice_id, output_path)
    elif config.voice_provider == VoiceProvider.ELEVENLABS:
        await synthesize_elevenlabs(segment.text, config.voice_id, output_path)
    elif config.voice_provider == VoiceProvider.SILICONFLOW:
        await synthesize_siliconflow(segment.text, config.voice_id, output_path)
    else:
        raise ConfigError(f"Unsupported voice provider: {config.voice_provider}")

    return output_path


async def synthesize_script(
    segments: list[ScriptSegment],
    config: VoiceConfig,
    output_dir: Path,
) -> list[Path]:
    """Synthesize all segments sequentially (one TTS call per segment)."""
    paths: list[Path] = []
    for seg in segments:
        path = await synthesize_segment(seg, config, output_dir)
        paths.append(path)
    return paths


async def list_providers() -> list[dict[str, Any]]:
    """Return the catalogue of voice providers for /voice/providers."""
    catalogue = [
        {
            "id": "edge",
            "name": "Edge TTS (Microsoft)",
            "requires_key": False,
            "available": True,
            "voices": EDGE_VOICES,
        },
        {
            "id": "azure",
            "name": "Azure Speech",
            "requires_key": True,
            "available": bool(settings.azure_speech_key),
            "voices": [],
        },
        {
            "id": "elevenlabs",
            "name": "ElevenLabs",
            "requires_key": True,
            "available": bool(settings.elevenlabs_api_key),
            "voices": [],
        },
        {
            "id": "siliconflow",
            "name": "SiliconFlow",
            "requires_key": True,
            "available": bool(settings.siliconflow_api_key),
            "voices": [],
        },
    ]
    for c in catalogue:
        c["active"] = settings.voice_provider == c["id"]
    return catalogue