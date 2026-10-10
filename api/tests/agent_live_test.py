"""Live agent test — exercises DeepSeek function calling end to end.

Requires DEEPSEEK_API_KEY in the environment. Does NOT run the video pipeline;
it only verifies the model picks the right tools and the loop returns a reply.

    python3 tests/agent_live_test.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("VIDIFORGE_API_TOKEN", "test-token-12345678")
os.environ.setdefault("GCS_BUCKET", "")

from app.models.schema import VideoRequest  # noqa: E402
from app.services import agent as agent_service  # noqa: E402


def main() -> int:
    if not os.environ.get("DEEPSEEK_API_KEY"):
        print("SKIP: DEEPSEEK_API_KEY not set")
        return 0

    scheduled: list[tuple[str, VideoRequest]] = []

    def schedule(task_id: str, request: VideoRequest) -> None:
        # Record instead of running — we only check the model's decisions here.
        scheduled.append((task_id, request))

    cases = [
        ("建立一支關於北歐家居的短影片", "create_video"),
        ("我最近做了哪些影片？", "list_tasks"),
        ("給我幾個咖啡主題的英文素材關鍵詞", "suggest_keywords"),
    ]

    failures = 0
    for prompt, expected in cases:
        print(f"\n> {prompt}")
        result = asyncio.run(
            agent_service.chat(
                messages=[{"role": "user", "content": prompt}],
                model="deepseek-flash",
                schedule=schedule,
            )
        )
        called = [c["tool"] for c in result.get("tool_calls", [])]
        reply = (result.get("reply") or "").strip().replace("\n", " ")[:90]
        ok = expected in called
        print(f"  model : {result.get('model')}")
        print(f"  tools : {called or '(none)'}")
        print(f"  reply : {reply}")
        print(f"  {'PASS' if ok else 'FAIL'}  expected tool {expected}")
        if not ok:
            failures += 1

    if scheduled:
        tid, req = scheduled[0]
        print(f"\n  scheduled task : {tid[:8]}…  topic={req.topic!r} aspect={req.aspect.value}")

    print(f"\n{'=' * 46}\n{'PASSED' if not failures else f'FAILED {failures}'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
