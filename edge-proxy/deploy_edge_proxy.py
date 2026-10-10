#!/usr/bin/env python3
"""Deploy the VidiForge edge proxy to Vercel and attach the custom domain.

Everything goes through the Vercel REST API, so no interactive CLI prompts and
no local project setup are needed.

    cd edge-proxy
    VERCEL_TOKEN=... python3 deploy_edge_proxy.py
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

TEAM_ID = "team_hTLcXQ4mzASa2CItfUy2WiBL"
PROJECT = "vidiforge-edge"
DOMAIN = "vidiforge.mlcy5211.vip"
CLOUD_RUN = "https://vidiforge-cw33iwansa-de.a.run.app"

VERCEL_JSON = {
    "$schema": "https://openapi.vercel.sh/vercel.json",
    "rewrites": [{"source": "/(.*)", "destination": f"{CLOUD_RUN}/$1"}],
}
INDEX_HTML = (
    "<!doctype html><html><head><meta charset=\"utf-8\">"
    "<title>VidiForge</title></head><body>"
    "<p>VidiForge edge proxy. Requests are forwarded to the application.</p>"
    "</body></html>"
)


def api(method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
    token = os.environ.get("VERCEL_TOKEN")
    if not token:
        print("ERROR: VERCEL_TOKEN is not set")
        sys.exit(2)
    req = urllib.request.Request(
        f"https://api.vercel.com{path}",
        data=json.dumps(payload).encode() if payload is not None else None,
        method=method,
    )
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, {"raw": body[:600]}
    except urllib.error.URLError as e:
        return 0, {"error": str(e)}


def err(body: dict) -> str:
    e = body.get("error", body)
    if isinstance(e, dict):
        return f"{e.get('code', '')} {e.get('message', '')}".strip() or json.dumps(body)[:300]
    return str(e)[:300]


def main() -> int:
    print(f"proxy   : {PROJECT}")
    print(f"target  : {CLOUD_RUN}")
    print(f"domain  : {DOMAIN}\n")

    # 1 ── project ----------------------------------------------------------
    print("[1/4] project …")
    st, body = api("GET", f"/v9/projects/{PROJECT}?teamId={TEAM_ID}")
    if st == 200:
        print(f"       exists (id={body.get('id')})")
    else:
        st, body = api(
            "POST", f"/v11/projects?teamId={TEAM_ID}", {"name": PROJECT, "framework": None}
        )
        if st not in (200, 201):
            print(f"       FAIL: {err(body)}")
            return 1
        print(f"       created (id={body.get('id')})")

    # 2 ── deployment -------------------------------------------------------
    print("[2/4] deployment …")
    st, dep = api(
        "POST",
        f"/v13/deployments?teamId={TEAM_ID}&forceNew=1",
        {
            "name": PROJECT,
            "target": "production",
            "files": [
                {"file": "vercel.json", "data": json.dumps(VERCEL_JSON)},
                {"file": "index.html", "data": INDEX_HTML},
            ],
            "projectSettings": {"framework": None},
        },
    )
    if st not in (200, 201):
        print(f"       FAIL: {err(dep)}")
        return 1
    dep_id, dep_url = dep.get("id"), dep.get("url")
    print(f"       queued {dep_url}")

    # wait for the build to finish
    for _ in range(30):
        st, cur = api("GET", f"/v13/deployments/{dep_id}?teamId={TEAM_ID}")
        state = (cur or {}).get("readyState") or (cur or {}).get("status")
        if state in ("READY", "ERROR", "CANCELED"):
            break
        print(f"       … {state}")
        time.sleep(5)
    print(f"       state: {state}")
    if state != "READY":
        print("       deployment did not become ready")
        return 1

    # 3 ── domain -----------------------------------------------------------
    print("[3/4] attach domain …")
    st, body = api(
        "POST", f"/v10/projects/{PROJECT}/domains?teamId={TEAM_ID}", {"name": DOMAIN}
    )
    if st in (200, 201):
        print("       attached")
    elif "already" in err(body).lower():
        print("       already attached")
    else:
        print(f"       FAIL: {err(body)}")
        return 1

    # 4 ── report -----------------------------------------------------------
    print("[4/4] verify …")
    st, cfg = api("GET", f"/v5/domains/{DOMAIN}/config?teamId={TEAM_ID}")
    if st == 200:
        print(f"       configuredBy : {cfg.get('configuredBy')}")
        print(f"       misconfigured: {cfg.get('misconfigured')}")

    print("\nDone. Test with:")
    print(f"  curl -s https://{DOMAIN}/health")
    return 0


if __name__ == "__main__":
    sys.exit(main())
