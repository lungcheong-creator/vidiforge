"""Pipeline orchestrator. Runs the 6-stage video generation pipeline:

  script → voice → footage → subtitle → bgm → render
"""

from __future__ import annotations

import asyncio
import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.config.config import settings
from app.db.database import session_scope
from app.db.models import Task
from app.models.const import TaskStatus
from app.models.exception import TaskError
from app.models.schema import Script, VideoRequest, VideoTask, TaskStage
from app.services import bgm, llm, material, subtitle, voice, video
from app.services.state import TaskState


STAGES = [
    ("script", 5, 15),
    ("voice", 15, 35),
    ("footage", 35, 55),
    ("subtitle", 55, 70),
    ("bgm", 70, 75),
    ("render", 75, 100),
]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def run_pipeline(task_id: str, request: VideoRequest) -> None:
    """Run the full pipeline for one task. Persists progress to the Task row."""
    state = TaskState(task_id)
    task_dir = settings.outputs_path / task_id
    work_dir = settings.cache_path / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    byok = request.api_keys or {}

    try:
        state.update(status=TaskStatus.RUNNING, progress=0)

        # ===== STAGE 1: SCRIPT =====
        state.update(current_stage="script", progress=STAGES[0][1])
        if request.script:
            script = request.script
        else:
            script = await llm.generate_script(
                topic=request.topic,
                keywords=request.keywords,
                provider=request.llm_provider,
                language=request.language.value,
                segment_count=request.segments,
                byok=byok,
            )
        state.update(script_json=script.model_dump_json())

        # ===== STAGE 2: VOICE =====
        state.update(current_stage="voice", progress=STAGES[1][1])
        voice_dir = work_dir / "voice"
        voice_paths = await voice.synthesize_script(script.segments, request.voice, voice_dir)
        if not voice_paths:
            raise TaskError("Voice synthesis produced no output.")
        # Concatenate all voice segments into one track
        full_voice = work_dir / "voice_full.mp3"
        await video.concatenate_voice_segments(voice_paths, full_voice)
        state.update(progress=STAGES[2][1])

        # ===== STAGE 3: FOOTAGE =====
        state.update(current_stage="footage", progress=STAGES[2][1])
        footage_dir = work_dir / "footage"
        # Try API-based footage first; if Pexels key missing, fallback to gradient
        footage_paths = await material.fetch_footage_for_script(
            script.segments, request.material, footage_dir
        )
        # Fill any missing segments with a generated solid-color fallback
        if not all(footage_paths):
            await _generate_fallback_footage(
                [s for s, p in zip(script.segments, footage_paths) if not p],
                footage_dir,
                request.aspect.value,
            )
            rebuilt = []
            for s, p in zip(script.segments, footage_paths):
                rebuilt.append(p if p and p.exists() else footage_dir / f"seg_{s.id:03d}_fallback.mp4")
            footage_paths = rebuilt
        state.update(progress=STAGES[3][1])

        # ===== STAGE 4: SUBTITLE =====
        state.update(current_stage="subtitle", progress=STAGES[3][1])
        ass_path = work_dir / "subtitle.ass"
        from app.utils.ffmpeg import probe_duration
        video_width, video_height = {
            "9:16": (1080, 1920),
            "16:9": (1920, 1080),
            "1:1": (1080, 1080),
        }.get(request.aspect.value, (1080, 1920))

        # Use concatenated voice track + its duration for cue alignment
        total_dur = probe_duration(full_voice) or sum(s.duration for s in script.segments)
        await subtitle.generate_subtitles_for_segments(
            segments=script.segments,
            voice_paths=voice_paths,
            config=request.subtitle,
            output_ass_path=ass_path,
            language=request.language.value.split("-")[0],
            video_width=video_width,
            video_height=video_height,
        )
        state.update(progress=STAGES[4][1])

        # ===== STAGE 5: BGM =====
        state.update(current_stage="bgm", progress=STAGES[4][1])
        bgm_path = bgm.pick_bgm(request.bgm)
        state.update(progress=STAGES[5][1])

        # ===== STAGE 6: RENDER =====
        state.update(current_stage="render", progress=STAGES[5][1])
        final_path = await video.compose_full_video(
            footage_clips=footage_paths,
            voice_track=full_voice,
            bgm_path=bgm_path,
            subtitle_path=ass_path,
            aspect=request.aspect.value,
            target_duration=total_dur,
            output_dir=task_dir,
            work_dir=work_dir,
        )

        # Persist final state
        file_size = final_path.stat().st_size if final_path.exists() else 0
        duration = probe_duration(final_path) or total_dur
        rel_path = str(final_path.relative_to(settings.storage_root.parent))
        state.update(
            status=TaskStatus.DONE,
            progress=100,
            current_stage=None,
            output_path=rel_path,
            duration=duration,
            file_size=file_size,
        )

    except Exception as e:
        state.update(status=TaskStatus.FAILED, error=str(e))
        raise


async def _generate_fallback_footage(
    missing_segments: list,  # list[ScriptSegment]
    output_dir: Path,
    aspect: str,
) -> None:
    """Generate solid-color (warm gradient) fallback clips using FFmpeg."""
    width, height = {"9:16": (540, 960), "16:9": (960, 540), "1:1": (540, 540)}.get(aspect, (540, 960))
    palette = ["#F5EFE6", "#E8DFD2", "#DACBB7", "#C45A3E", "#5B5238", "#A06030"]

    for i, seg in enumerate(missing_segments):
        out = output_dir / f"seg_{seg.id:03d}_fallback.mp4"
        if out.exists():
            continue
        color = palette[i % len(palette)].lstrip("#")
        # 5-second fade-through-color clip
        args = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi",
            "-i", f"color=c=0x{color}:s={width}x{height}:d=5:r=24",
            "-vf", f"fade=t=in:st=0:d=0.5,format=yuv420p",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-t", "5",
            str(out),
        ]
        try:
            import subprocess
            subprocess.run(args, check=True, capture_output=True, timeout=30)
        except Exception:
            # Soft fail; pipeline will still run but with missing clips
            pass


async def create_task(request: VideoRequest) -> VideoTask:
    """Create a new task row and return its representation."""
    task_id = uuid.uuid4().hex
    config_json = request.model_dump_json()
    now = _utcnow()

    with session_scope() as s:
        task = Task(
            id=task_id,
            topic=request.topic,
            aspect=request.aspect.value,
            status=TaskStatus.PENDING.value,
            progress=0,
            config_json=config_json,
            created_at=now,
            updated_at=now,
        )
        s.add(task)
        s.commit()

    return await get_task(task_id)


async def get_task(task_id: str) -> VideoTask:
    with session_scope() as s:
        task = s.get(Task, task_id)
        if not task:
            raise TaskError(f"Task {task_id} not found")

        script = None
        if task.script_json:
            try:
                script = Script.model_validate_json(task.script_json)
            except Exception:
                script = None

        stages = [
            TaskStage(name=stage[0], status=TaskStatus.DONE if task.progress >= stage[2] else (
                TaskStatus.RUNNING if task.progress >= stage[1] else TaskStatus.PENDING
            ), progress=min(100, max(0, int((task.progress - stage[1]) / max(1, (stage[2] - stage[1])) * 100))))
            for stage in STAGES
        ]

        output_url = None
        if task.output_path:
            output_url = f"/api/v1/stream/{task.output_path}"

        return VideoTask(
            id=task.id,
            topic=task.topic,
            aspect=task.aspect,  # type: ignore[arg-type]
            status=task.status,  # type: ignore[arg-type]
            progress=task.progress,
            current_stage=task.current_stage,
            script=script,
            output_path=task.output_path,
            output_url=output_url,
            duration=task.duration,
            file_size=task.file_size,
            stages=stages,
            error=task.error,
            config=json.loads(task.config_json) if task.config_json else None,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )


async def list_tasks(limit: int = 50, offset: int = 0) -> tuple[int, list[VideoTask]]:
    from sqlmodel import select
    with session_scope() as s:
        stmt = select(Task).order_by(Task.created_at.desc()).offset(offset).limit(limit)
        rows = list(s.exec(stmt))
        total_stmt = select(Task)
        total = len(list(s.exec(total_stmt)))
        tasks = [await get_task(r.id) for r in rows]
        return total, tasks


async def delete_task(task_id: str) -> None:
    with session_scope() as s:
        task = s.get(Task, task_id)
        if task:
            s.delete(task)
            s.commit()
    # Cleanup files
    out_dir = settings.outputs_path / task_id
    work_dir = settings.cache_path / task_id
    if out_dir.exists():
        shutil.rmtree(out_dir, ignore_errors=True)
    if work_dir.exists():
        shutil.rmtree(work_dir, ignore_errors=True)