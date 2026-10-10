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


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def call(base: str, token: str, path: str, method: str = "GET",
         body: dict | None = None, follow: bool = True):
    """Call the API. Returns (status, parsed_json_or_None, raw_bytes)."""
    req = urllib.request.Request(
        f"{base.rstrip('/')}{path}",
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
    )
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")

    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=90) as r:
            raw = r.read()
            try:
                return r.status, json.loads(raw) if raw else {}, raw
            except (json.JSONDecodeError, UnicodeDecodeError):
                return r.status, None, raw
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw), raw
        except (json.JSONDecodeError, UnicodeDecodeError):
            return e.code, None, raw


def main() -> int:
    base, token = sys.argv[1], sys.argv[2]

    print("\n[1] health")
    st, body, _ = call(base, token, "/health")
    check("GET /health", st == 200 and body and body.get("ok") is True, str(body)[:120])

    print("\n[2] auth")
    st, _, _ = call(base, "wrong-token", "/api/v1/tasks")
    check("bad token -> 401", st == 401, f"got {st}")

    print("\n[3] providers & models")
    st, providers, _ = call(base, token, "/api/v1/llm/providers")
    check("llm providers", st == 200 and isinstance(providers, list))
    st, models, _ = call(base, token, "/api/v1/llm/models")
    ids = {m["id"] for m in models} if isinstance(models, list) else set()
    check("deepseek-flash listed", "deepseek-flash" in ids, str(ids))
    st, voice, _ = call(base, token, "/api/v1/voice/providers")
    check("voice providers", st == 200 and isinstance(voice, list))
    st, mats, _ = call(base, token, "/api/v1/materials/providers")
    check("material providers", st == 200)

    print("\n[4] agent tools exposed")
    st, tools, _ = call(base, token, "/api/v1/agent/tools")
    names = {t["name"] for t in tools} if isinstance(tools, list) else set()
    check("agent tools", st == 200 and "create_video" in names, str(names))

    print("\n[5] create a video (GCS-backed)")
    st, task, _ = call(
        base, token, "/api/v1/videos", "POST",
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
    check("POST /videos", st in (200, 201) and task and task.get("id"), str(task)[:160])
    tid = (task or {}).get("id")
    if not tid:
        return summarise()

    print(f"\n[6] poll task {tid[:10]}…")
    final: dict = {}
    for i in range(24):
        st, cur, _ = call(base, token, f"/api/v1/tasks/{tid}")
        final = cur or {}
        status = final.get("status")
        print(f"    [{i}] {status} {final.get('progress')}% {final.get('current_stage') or ''}")
        if status in ("done", "failed"):
            break
        time.sleep(10)
    check("task completed", final.get("status") == "done", str(final.get("error"))[:200])

    print("\n[7] durable output")
    key = final.get("output_path")
    check("output key is a GCS object", bool(key) and str(key).startswith("tasks/"), str(key))
    check("file_size present", bool(final.get("file_size")), str(final.get("file_size")))

    print("\n[8] download")
    if key:
        st, _, raw = call(base, token, f"/api/v1/tasks/{tid}/file", follow=True)
        is_mp4 = b"ftyp" in raw[:32]
        check("task file returns playable MP4", st == 200 and is_mp4 and len(raw) > 10_000,
              f"http={st} bytes={len(raw)}")
        print(f"    downloaded {len(raw):,} bytes")

        st, _, raw2 = call(base, token, f"/api/v1/stream/{key}", follow=True)
        check("stream endpoint returns MP4", st == 200 and len(raw2) > 10_000,
              f"http={st} bytes={len(raw2)}")

        print("\n[8b] no credentials")
        st, _, _ = call(base, "wrong-token", f"/api/v1/download/{key}", follow=False)
        check("unauthenticated download rejected", st == 401, f"got {st}")

    print("\n[9] task list survives")
    st, listing, _ = call(base, token, "/api/v1/tasks?limit=5")
    ids = [t["id"] for t in listing.get("tasks", [])] if isinstance(listing, dict) else []
    check("task appears in list", tid in ids, f"{len(ids)} tasks")

    print("\n[10] batches")
    st, batch, _ = call(
        base, token, "/api/v1/batches", "POST",
        {"name": "驗證批次", "topics": ["清晨的窗邊"], "duration": 12, "segments": 2},
    )
    check("POST /batches", st == 201 and batch and batch.get("id"), str(batch)[:160])

    print("\n[11] settings round-trip")
    st, saved, _ = call(base, token, "/api/v1/settings/keys", "POST",
                        {"provider": "pexels", "value": "pex-test-1234567890"})
    check("save key", st == 200 and saved and saved.get("has_value"))
    st, keys, _ = call(base, token, "/api/v1/settings/keys")
    check("key listed as masked",
          st == 200 and any(k["provider"] == "pexels" and "pex-test-1234567890" not in json.dumps(k)
                            for k in (keys or [])))
    st, status, _ = call(base, token, "/api/v1/settings/providers/status")
    check("provider status", st == 200 and "pexels" in (status or {}).get("configured", []))

    return summarise()


def summarise() -> int:
    print(f"\n{'=' * 48}")
    print(f"PASSED {len(PASS)}   FAILED {len(FAIL)}")
    for f in FAIL:
        print(f"  - {f}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
