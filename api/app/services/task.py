"""Pipeline orchestrator. Runs the video generation pipeline:

  script → voice → footage → subtitle → bgm → render → upload

Task metadata and rendered output are persisted through `tasks_repo` /
`blobstore` so they survive instance restarts.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config.config import settings
from app.models.const import TaskStatus
from app.models.exception import TaskError
from app.models.schema import Script, VideoRequest, VideoTask
from app.services import bgm, blobstore, llm, material, subtitle, tasks_repo, voice, video
from app.services.state import TaskState


log = logging.getLogger("vidiforge.pipeline")

STAGES = [
    ("script", 5, 15),
    ("voice", 15, 35),
    ("footage", 35, 55),
    ("subtitle", 55, 70),
    ("bgm", 70, 75),
    ("render", 75, 100),
]


async def run_pipeline(task_id: str, request: VideoRequest) -> None:
    """Run the full pipeline for one task, reporting progress as it goes."""
    state = TaskState(task_id)
    work_dir = settings.cache_path / task_id
    work_dir.mkdir(parents=True, exist_ok=True)

    try:
        state.update(status=TaskStatus.RUNNING, progress=0)

        # ===== 1. SCRIPT =====
        state.update(current_stage="script", progress=STAGES[0][1])
        if request.script:
            script = request.script
        else:
            script = await llm.generate_script(
                topic=request.topic,
                keywords=request.keywords,
                provider=request.llm_provider,
                model=request.llm_model or None,
                language=request.language.value,
                segment_count=request.segments,
                byok=request.api_keys or {},
            )
        state.update(script=script.model_dump())

        # ===== 2. VOICE =====
        state.update(current_stage="voice", progress=STAGES[1][1])
        voice_paths = await voice.synthesize_script(
            script.segments, request.voice, work_dir / "voice"
        )
        if not voice_paths:
            raise TaskError("Voice synthesis produced no output.")
        full_voice = work_dir / "voice_full.mp3"
        await video.concatenate_voice_segments(voice_paths, full_voice)
        state.update(progress=STAGES[2][1])

        # ===== 3. FOOTAGE =====
        state.update(current_stage="footage", progress=STAGES[2][1])
        footage_dir = work_dir / "footage"
        footage_paths = await material.fetch_footage_for_script(
            script.segments, request.material, footage_dir
        )
        if not all(footage_paths):
            missing = [s for s, p in zip(script.segments, footage_paths) if not (p and p.is_file())]
            await _generate_fallback_footage(missing, footage_dir, request.aspect.value)
            rebuilt: list[Path | None] = []
            for s, p in zip(script.segments, footage_paths):
                fallback = footage_dir / f"seg_{s.id:03d}_fallback.mp4"
                if p is not None and p.is_file():
                    rebuilt.append(p)
                elif fallback.is_file():
                    rebuilt.append(fallback)
                else:
                    rebuilt.append(None)
            footage_paths = rebuilt
        state.update(progress=STAGES[3][1])

        # ===== 4. SUBTITLE =====
        state.update(current_stage="subtitle", progress=STAGES[3][1])
        from app.utils.ffmpeg import probe_duration

        video_width, video_height = {
            "9:16": (1080, 1920),
            "16:9": (1920, 1080),
            "1:1": (1080, 1080),
        }.get(request.aspect.value, (1080, 1920))

        ass_path = work_dir / "subtitle.ass"
        await subtitle.generate_subtitles_for_segments(
            segments=script.segments,
            voice_paths=voice_paths,
            config=request.subtitle,
            output_ass_path=ass_path,
            language=request.language.value.split("-")[0],
            video_width=video_width,
            video_height=video_height,
            voice_id=request.voice.voice_id,
        )
        total_dur = probe_duration(full_voice) or float(sum(s.duration for s in script.segments)) or 15.0
        state.update(progress=STAGES[4][1])

        # ===== 5. BGM =====
        state.update(current_stage="bgm", progress=STAGES[4][1])
        bgm_path = bgm.pick_bgm(request.bgm)
        state.update(progress=STAGES[5][1])

        # ===== 6. RENDER =====
        state.update(current_stage="render", progress=STAGES[5][1])
        final_path = await video.compose_full_video(
            footage_clips=footage_paths,
            voice_track=full_voice,
            bgm_path=bgm_path,
            subtitle_path=ass_path,
            aspect=request.aspect.value,
            target_duration=total_dur,
            output_dir=work_dir / "out",
            work_dir=work_dir,
        )

        # ===== 7. UPLOAD (durable) =====
        state.update(current_stage="upload", progress=96)
        key = tasks_repo.output_key(task_id, final_path.name)
        blobstore.upload_file(final_path, key, content_type="video/mp4")
        duration = probe_duration(final_path) or total_dur

        state.update(
            status=TaskStatus.DONE,
            progress=100,
            clear_stage=True,
            output_key=key,
            output_url=f"/api/v1/tasks/{task_id}/file",
            duration=duration,
            file_size=final_path.stat().st_size,
        )
        log.info("task %s finished -> %s", task_id, key)

    except Exception as e:
        log.exception("pipeline failed for task %s", task_id)
        state.update(status=TaskStatus.FAILED, error=str(e))
        raise
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


async def _generate_fallback_footage(
    missing_segments: list,  # list[ScriptSegment]
    output_dir: Path,
    aspect: str,
) -> None:
    """Generate solid-colour fallback clips with FFmpeg when no footage is available."""
    import subprocess

    from app.utils.ffmpeg import get_ffmpeg_binary

    width, height = {"9:16": (540, 960), "16:9": (960, 540), "1:1": (540, 540)}.get(
        aspect, (540, 960)
    )
    palette = ["F5EFE6", "E8DFD2", "DACBB7", "C45A3E", "5B5238", "A06030"]
    ffmpeg_bin = get_ffmpeg_binary()
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, seg in enumerate(missing_segments):
        out = output_dir / f"seg_{seg.id:03d}_fallback.mp4"
        if out.is_file():
            continue
        colour = palette[i % len(palette)]
        args = [
            ffmpeg_bin, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi",
            "-i", f"color=c=0x{colour}:s={width}x{height}:d=5:r=24",
            "-vf", "fade=t=in:st=0:d=0.5,format=yuv420p",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-t", "5", str(out),
        ]
        try:
            subprocess.run(args, check=True, capture_output=True, timeout=60)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
            log.warning("fallback clip failed for segment %s: %s", seg.id, e)


# --------------------------------------------------------------- task API


def _to_model(raw: dict[str, Any]) -> VideoTask:
    script = None
    if isinstance(raw.get("script"), dict):
        try:
            script = Script.model_validate(raw["script"])
        except Exception:
            script = None

    progress = int(raw.get("progress") or 0)
    stage = raw.get("current_stage")

    stages = []
    for name, lo, hi in STAGES:
        if progress >= hi:
            st, sp = TaskStatus.DONE, 100
        elif stage == name:
            st = TaskStatus.RUNNING
            sp = int((progress - lo) / max(1, hi - lo) * 100)
        else:
            st, sp = TaskStatus.PENDING, 0
        stages.append({"name": name, "status": st.value, "progress": max(0, min(100, sp))})

    return VideoTask(
        id=raw["id"],
        topic=raw.get("topic", ""),
        aspect=raw.get("aspect", "9:16"),
        status=raw.get("status", "pending"),
        progress=progress,
        current_stage=stage,
        script=script,
        output_path=raw.get("output_path"),
        output_url=raw.get("output_url"),
        duration=raw.get("duration"),
        file_size=raw.get("file_size"),
        stages=stages,
        error=raw.get("error"),
        config=raw.get("config"),
        created_at=raw.get("created_at") or datetime.now(timezone.utc).isoformat(),
        updated_at=raw.get("updated_at") or datetime.now(timezone.utc).isoformat(),
    )


async def create_task(request: VideoRequest) -> VideoTask:
    raw = tasks_repo.create(
        topic=request.topic,
        aspect=request.aspect.value,
        config=request.model_dump(mode="json"),
    )
    return _to_model(raw)


async def get_task(task_id: str) -> VideoTask:
    raw = tasks_repo.get(task_id)
    if raw is None:
        raise TaskError(f"Task {task_id} not found")
    return _to_model(raw)


async def list_tasks(limit: int = 50, offset: int = 0) -> tuple[int, list[VideoTask]]:
    total, raws = tasks_repo.list_tasks(limit=limit, offset=offset)
    return total, [_to_model(r) for r in raws]


async def delete_task(task_id: str) -> None:
    tasks_repo.delete(task_id)
