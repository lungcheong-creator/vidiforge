"""Integration test for the GCS-backed task store, batches and the agent tools.

Runs with the blob store in local-fallback mode (GCS_BUCKET unset) so no cloud
access is needed.

    python3 tests/integration_test.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("VIDIFORGE_API_TOKEN", "test-token-12345678")
os.environ.setdefault("GCS_BUCKET", "")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

TOKEN = os.environ["VIDIFORGE_API_TOKEN"]
H = {"Authorization": f"Bearer {TOKEN}"}
PASS, FAIL = [], []


def check(name: str, ok: bool, detail: str = "") -> None:
    (PASS if ok else FAIL).append(name)
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{(' — ' + detail) if detail and not ok else ''}")


def main() -> int:
    with TestClient(app) as c:
        print("\n[1] health / meta")
        r = c.get("/health")
        check("GET /health", r.status_code == 200 and r.json().get("ok") is True, r.text[:120])

        print("\n[2] auth")
        check("no token -> 401", c.get("/api/v1/tasks").status_code == 401)

        print("\n[3] task store (GCS-backed repo)")
        from app.services import tasks_repo

        t = tasks_repo.create(topic="整合測試主題", aspect="9:16", config={"x": 1})
        check("create task", bool(t.get("id")))
        got = tasks_repo.get(t["id"])
        check("read task back", got is not None and got["topic"] == "整合測試主題")
        tasks_repo.update(t["id"], progress=42, status="running")
        check("update task", tasks_repo.get(t["id"])["progress"] == 42)
        total, items = tasks_repo.list_tasks(limit=10)
        check("list tasks", total >= 1 and any(i["id"] == t["id"] for i in items))

        print("\n[4] task API")
        r = c.get(f"/api/v1/tasks/{t['id']}", headers=H)
        check("GET /tasks/{id}", r.status_code == 200 and r.json()["progress"] == 42, r.text[:120])
        r = c.get("/api/v1/tasks?limit=5", headers=H)
        check("GET /tasks", r.status_code == 200 and "tasks" in r.json())

        print("\n[5] blob store")
        from app.services import blobstore

        key = f"tasks/{t['id']}/probe.txt"
        blobstore.put_bytes(key, b"hello-vidiforge")
        check("put/get bytes", blobstore.get_bytes(key) == b"hello-vidiforge")
        keys = blobstore.list_keys("tasks/", suffix="/probe.txt")
        check("list keys", key in keys)
        check("delete prefix", blobstore.delete_prefix(f"tasks/{t['id']}/") >= 1)

        print("\n[6] batches")
        r = c.post(
            "/api/v1/batches",
            headers=H,
            json={"name": "整合批次", "topics": ["主題一", "主題二"], "duration": 10, "segments": 2},
        )
        check("POST /batches", r.status_code == 201, r.text[:160])
        batch = r.json() if r.status_code == 201 else {}
        bid = batch.get("id")
        if bid:
            r = c.get(f"/api/v1/batches/{bid}", headers=H)
            check("GET /batches/{id}", r.status_code == 200 and r.json()["total"] == 2)
            r = c.get("/api/v1/batches", headers=H)
            check("GET /batches", r.status_code == 200 and r.json()["total"] >= 1)

        print("\n[7] agent tools")
        r = c.get("/api/v1/agent/tools", headers=H)
        names = {x["name"] for x in r.json()} if r.status_code == 200 else set()
        check("GET /agent/tools", r.status_code == 200 and "create_video" in names, str(names))

        from app.services import agent as agent_service

        res = agent_service._exec_list_tasks({"limit": 5})
        check("tool list_tasks", "tasks" in res and res["count"] >= 1)
        res = agent_service._exec_suggest_keywords({"topic": "北歐家居"})
        check("tool suggest_keywords", len(res.get("keywords", [])) == 5)
        req = agent_service._build_request({"topic": "貓咪日常", "aspect": "1:1", "duration": 12})
        check(
            "tool create_video payload",
            req.topic == "貓咪日常" and req.aspect.value == "1:1" and req.duration == 12,
        )

        print("\n[8] llm models catalogue")
        r = c.get("/api/v1/llm/models", headers=H)
        ids = {m["id"] for m in r.json()} if r.status_code == 200 else set()
        check("GET /llm/models", "deepseek-flash" in ids, str(ids))

        print("\n[9] openapi")
        r = c.get("/openapi.json")
        check("OpenAPI schema", r.status_code == 200 and "/api/v1/batches" in r.json()["paths"])

    print(f"\n{'=' * 46}")
    print(f"PASSED {len(PASS)}   FAILED {len(FAIL)}")
    if FAIL:
        print("failures:")
        for f in FAIL:
            print(f"  - {f}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
