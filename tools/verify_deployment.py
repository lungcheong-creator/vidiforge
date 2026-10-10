#!/usr/bin/env python3
"""End-to-end check against the deployed VidiForge service.

Usage:  python3 verify_deployment.py <base-url> <api-token>
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

PASS, FAIL = [], []


def check(name: str, ok: bool, detail: str = "") -> None:
    (PASS if ok else FAIL).append(name)
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail and not ok else ""))


def call(base: str, token: str, path: str, method: str = "GET", body: dict | None = None):
    req = urllib.request.Request(
        f"{base.rstrip('/')}{path}",
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
    )
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            return r.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return e.code, {"detail": e.read().decode()[:200]}


def main() -> int:
    base, token = sys.argv[1], sys.argv[2]

    print("\n[1] health")
    st, body = call(base, token, "/health")
    check("GET /health", st == 200 and body.get("ok") is True, str(body)[:120])

    print("\n[2] auth")
    st, _ = call(base, "wrong-token", "/api/v1/tasks")
    check("bad token -> 401", st == 401, f"got {st}")

    print("\n[3] providers & models")
    st, providers = call(base, token, "/api/v1/llm/providers")
    check("llm providers", st == 200 and isinstance(providers, list))
    st, models = call(base, token, "/api/v1/llm/models")
    ids = {m["id"] for m in models} if isinstance(models, list) else set()
    check("deepseek-flash listed", "deepseek-flash" in ids, str(ids))
    st, voice = call(base, token, "/api/v1/voice/providers")
    check("voice providers", st == 200 and isinstance(voice, list))
    st, mats = call(base, token, "/api/v1/materials/providers")
    check("material providers", st == 200)

    print("\n[4] agent tools exposed")
    st, tools = call(base, token, "/api/v1/agent/tools")
    names = {t["name"] for t in tools} if isinstance(tools, list) else set()
    check("agent tools", st == 200 and "create_video" in names, str(names))

    print("\n[5] create a video (GCS-backed)")
    st, task = call(
        base,
        token,
        "/api/v1/videos",
        "POST",
        {
            "topic": "雨天的咖啡館",
            "keywords": ["coffee", "rain"],
            "language": "zh-CN",
            "aspect": "9:16",
            "duration": 18,
            "segments": 3,
            "llm_provider": "deepseek",
            "llm_model": "deepseek-flash",
            "script": None,
            "voice": {"provider": "edge", "voice_id": "zh-CN-XiaoxiaoNeural", "speed": 1.0, "pitch": 0.0},
            "subtitle": {
                "provider": "edge", "font": "Noto Sans CJK SC", "font_size": 48,
                "font_color": "#FFFFFF", "position": "bottom",
                "outline_color": "#000000", "outline_width": 2,
            },
            "material": {"provider": "pexels", "orientation": "portrait"},
            "bgm": {"enabled": False, "volume": 0.3, "random": True, "path": None},
            "api_keys": {},
        },
    )
    check("POST /videos", st in (200, 201) and task.get("id"), str(task)[:160])
    tid = task.get("id")
    if not tid:
        return summarise()

    print(f"\n[6] poll task {tid[:10]}…")
    final = {}
    for i in range(24):
        st, cur = call(base, token, f"/api/v1/tasks/{tid}")
        final = cur
        status = cur.get("status")
        print(f"    [{i}] {status} {cur.get('progress')}% {cur.get('current_stage') or ''}")
        if status in ("done", "failed"):
            break
        time.sleep(10)
    check("task completed", final.get("status") == "done", str(final.get("error"))[:200])

    print("\n[7] durable output")
    key = final.get("output_path")
    check("output key is a GCS object", bool(key) and key.startswith("tasks/"), str(key))
    check("file_size present", bool(final.get("file_size")), str(final.get("file_size")))

    print("\n[8] download resolution")
    st, _ = call(base, token, f"/api/v1/tasks/{tid}/file")
    check("task file endpoint reachable", st in (200, 302, 307), f"got {st}")

    print("\n[9] task list survives")
    st, listing = call(base, token, "/api/v1/tasks?limit=5")
    ids = [t["id"] for t in listing.get("tasks", [])] if isinstance(listing, dict) else []
    check("task appears in list", tid in ids, f"{len(ids)} tasks")

    print("\n[10] batches")
    st, batch = call(
        base, token, "/api/v1/batches", "POST",
        {"name": "驗證批次", "topics": ["清晨的窗邊"], "duration": 12, "segments": 2},
    )
    check("POST /batches", st == 201 and batch.get("id"), str(batch)[:160])

    return summarise()


def summarise() -> int:
    print(f"\n{'=' * 48}")
    print(f"PASSED {len(PASS)}   FAILED {len(FAIL)}")
    for f in FAIL:
        print(f"  - {f}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
