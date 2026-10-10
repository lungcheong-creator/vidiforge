"""Subtitle service.

Two providers:
  - edge: parse edge-tts WordBoundary events for word-level timestamps.
  - whisper: fall back to faster-whisper for non-edge providers.

Outputs both an .ass subtitle file (for ffmpeg burning) and an SRT-format
string for the API response.
"""

from __future__ import annotations

import asyncio
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.config.config import settings
from app.models.const import SubtitleProvider
from app.models.exception import ProviderError
from app.models.schema import SubtitleConfig


@dataclass
class SubtitleCue:
    start: float  # seconds
    end: float    # seconds
    text: str


async def edge_word_timestamps(
    text: str, voice_id: str, audio_path: Path,
) -> list[SubtitleCue]:
    """Re-run edge-tts with detailed WordBoundary events to extract timestamps."""
    import edge_tts

    rate = "+0%"
    communicate = edge_tts.Communicate(text=text, voice=voice_id, rate=rate)
    cues: list[SubtitleCue] = []
    word_buffer: list[tuple[str, float, float]] = []

    async for evt in communicate.stream():
        if evt["type"] == "WordBoundary":
            offset = evt["offset"] / 10_000_000.0  # 100ns → seconds
            duration = evt["duration"] / 10_000_000.0
            text_part = evt["text"]
            word_buffer.append((text_part, offset, duration))
        elif evt["type"] == "audio":
            # Save audio bytes
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            with open(audio_path, "ab") as f:
                f.write(evt["data"])

    # Group words into short cues (3-5 words each)
    group_size = 4
    for i in range(0, len(word_buffer), group_size):
        chunk = word_buffer[i : i + group_size]
        if not chunk:
            continue
        text = " ".join(w[0] for w in chunk).strip()
        start = chunk[0][1]
        end = chunk[-1][1] + chunk[-1][2]
        cues.append(SubtitleCue(start=start, end=end, text=text))

    return cues


async def whisper_timestamps(audio_path: Path, language: str = "zh") -> list[SubtitleCue]:
    """Use faster-whisper to obtain word-level timestamps from an audio file."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise ProviderError("faster-whisper not installed") from e

    loop = asyncio.get_event_loop()

    def _run() -> list[SubtitleCue]:
        model = WhisperModel(settings.whisper_model_size, device="cpu", compute_type="int8")
        segments, _ = model.transcribe(str(audio_path), language=language, word_timestamps=True)
        cues: list[SubtitleCue] = []
        for seg in segments:
            if seg.words:
                for w in seg.words:
                    if w.word.strip():
                        cues.append(SubtitleCue(start=w.start, end=w.end, text=w.word.strip()))
        return cues

    return await loop.run_in_executor(None, _run)


def cues_to_srt(cues: list[SubtitleCue]) -> str:
    """Convert cues to SRT format."""
    def fmt(t: float) -> str:
        ms = int((t - int(t)) * 1000)
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    out = []
    for i, c in enumerate(cues, 1):
        out.append(f"{i}\n{fmt(c.start)} --> {fmt(c.end)}\n{c.text}\n")
    return "\n".join(out)


def cues_to_ass(
    cues: list[SubtitleCue],
    config: SubtitleConfig,
    video_width: int = 1080,
    video_height: int = 1920,
) -> str:
    """Convert cues to ASS subtitle format with the requested style."""
    font_map = {
        "bottom": 2,
        "center": 5,
        "top": 8,
    }
    alignment = font_map.get(config.position, 2)
    margin_v = 80

    # Resolve font family
    font = config.font
    if not any(c in font for c in ("Noto", "Source", "Fraunces", "Inter")):
        font = "Noto Sans CJK SC"

    color = config.font_color.lstrip("#")
    if len(color) == 6:
        color = "00" + color  # add alpha
    outline = config.outline_color.lstrip("#")
    if len(outline) == 6:
        outline = "00" + outline

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{config.font_size},&H00{color.upper()},&H000000FF,&H00{outline.upper()},&H80000000,-1,0,0,0,100,100,0,0,1,{config.outline_width},1,{alignment},40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def fmt(t: float) -> str:
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = t % 60
        return f"{h:d}:{m:02d}:{s:06.3f}"

    events = []
    for c in cues:
        events.append(
            f"Dialogue: 0,{fmt(c.start)},{fmt(c.end)},Default,,0,0,0,,{c.text.replace(chr(10), ' ')}"
        )
    return header + "\n".join(events)


async def generate_subtitles_for_script(
    *,
    script_text: str,
    voice_id: str,
    audio_path: Path,
    config: SubtitleConfig,
    output_ass_path: Path,
    language: str = "zh",
) -> tuple[list[SubtitleCue], Path]:
    """Generate subtitles for a single concatenated voice track.

    Returns (cues, ass_file_path).
    """
    provider = config.provider or SubtitleProvider(settings.subtitle_provider)

    if provider == SubtitleProvider.EDGE:
        cues = await edge_word_timestamps(script_text, voice_id, audio_path)
    elif provider == SubtitleProvider.WHISPER:
        cues = await whisper_timestamps(audio_path, language=language)
    else:
        raise ProviderError(f"Unsupported subtitle provider: {provider}")

    output_ass_path.parent.mkdir(parents=True, exist_ok=True)
    ass_content = cues_to_ass(cues, config)
    output_ass_path.write_text(ass_content, encoding="utf-8")

    return cues, output_ass_path


async def generate_subtitles_for_segments(
    *,
    segments: list,  # list[ScriptSegment]
    voice_paths: list[Path],
    config: SubtitleConfig,
    output_ass_path: Path,
    language: str = "zh",
    video_width: int = 1080,
    video_height: int = 1920,
) -> tuple[list[SubtitleCue], Path]:
    """Generate one cue list spanning all segments, with absolute timestamps."""
    cues: list[SubtitleCue] = []
    cumulative = 0.0
    for seg, audio_path in zip(segments, voice_paths):
        provider = config.provider or SubtitleProvider(settings.subtitle_provider)
        if provider == SubtitleProvider.EDGE:
            seg_cues = await edge_word_timestamps(seg.text, "zh-CN-XiaoxiaoNeural", audio_path)
        else:
            seg_cues = await whisper_timestamps(audio_path, language=language)
        for c in seg_cues:
            cues.append(SubtitleCue(start=c.start + cumulative, end=c.end + cumulative, text=c.text))
        # Estimate by audio duration (fallback: 5s per segment)
        from app.utils.ffmpeg import probe_duration
        d = probe_duration(audio_path)
        cumulative += d if d > 0 else 5.0

    output_ass_path.parent.mkdir(parents=True, exist_ok=True)
    ass_content = cues_to_ass(cues, config, video_width, video_height)
    output_ass_path.write_text(ass_content, encoding="utf-8")
    return cues, output_ass_path