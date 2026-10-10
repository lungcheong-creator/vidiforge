"""Local smoke test for the FFmpeg composition pipeline.

Builds fallback clips + a silent voice track + a subtitle file, then runs
`compose_full_video` and verifies the resulting MP4.

Run from the api/ directory:
    python3 tests/local_pipeline_test.py
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.video import compose_full_video  # noqa: E402
from app.utils.ffmpeg import get_ffmpeg_binary, probe_duration  # noqa: E402

ASS_TEMPLATE = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,2,40,40,80,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:04.00,Default,,0,0,0,,Test subtitle one
Dialogue: 0,0:00:04.00,0:00:08.00,Default,,0,0,0,,Test subtitle two
"""


def make_clip(ff: str, path: Path, colour: str, seconds: int = 5) -> None:
    subprocess.run(
        [
            ff, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi",
            "-i", f"color=c=0x{colour}:s=540x960:d={seconds}:r=24",
            "-vf", "format=yuv420p",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-t", str(seconds), str(path),
        ],
        check=True, capture_output=True, timeout=60,
    )


def make_silence(ff: str, path: Path, seconds: int = 15) -> None:
    subprocess.run(
        [
            ff, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
            "-t", str(seconds),
            "-c:a", "libmp3lame", "-b:a", "192k", str(path),
        ],
        check=True, capture_output=True, timeout=60,
    )


def main() -> int:
    ff = get_ffmpeg_binary()
    work = Path("/tmp/vf-pipe-test")
    foot = work / "footage"
    out = work / "out"
    for d in (foot, out):
        d.mkdir(parents=True, exist_ok=True)

    clips = []
    for i, colour in enumerate(["F5EFE6", "C45A3E", "5B5238"], start=1):
        p = foot / f"seg_{i:03d}_fallback.mp4"
        make_clip(ff, p, colour)
        clips.append(p)
    print(f"clips created: {[c.name for c in clips]}")

    voice = work / "voice_full.mp3"
    make_silence(ff, voice)
    print(f"voice track  : {round(probe_duration(voice), 2)}s")

    ass = work / "subtitle.ass"
    ass.write_text(ASS_TEMPLATE, encoding="utf-8")

    result = asyncio.run(
        compose_full_video(
            footage_clips=clips,
            voice_track=voice,
            bgm_path=None,
            subtitle_path=ass,
            aspect="9:16",
            target_duration=15.0,
            output_dir=out,
            work_dir=work / "work",
        )
    )

    size = result.stat().st_size if result.is_file() else 0
    duration = probe_duration(result)
    print(f"output       : {result.name}")
    print(f"exists       : {result.is_file()}")
    print(f"size         : {size} bytes")
    print(f"duration     : {round(duration, 2)}s")

    if not result.is_file() or size < 1000:
        print("FAIL: output missing or too small")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
