#!/usr/bin/env python3
"""Create the VidiForge edge-proxy deployment on Vercel and attach the custom domain.

The proxy forwards every request on vidiforge.mlcy5211.vip to the Cloud Run
service, so the whole app keeps a single public origin (no CORS, one URL).

Usage:  python3 deploy_edge_proxy.py
Reads VERCEL_TOKEN from the environment.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

TEAM_ID = "team_hTLcXQ4mzASa2CItfUy2WiBL"
PROJECT = "vidiforge"
DOMAIN = "vidiforge.mlcy5211.vip"
CLOUD_RUN = "https://vidiforge-cw33iwansa-de.a.run.app"

VERCEL_JSON = {
    "$schema": "https://openapi.vercel.sh/vercel.json",
    "rewrites": [{"source": "/(.*)", "destination": f"{CLOUD_RUN}/$1"}],
}

INDEX_HTML = (
    "<!doctype html><meta charset=utf-8>"
    "<title>VidiForge edge proxy</title>"
    "<p>Proxying to the VidiForge Cloud Run service.</p>"
)


def api(method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
    token = os.environ["VERCEL_TOKEN"]
    url = f"https://api.vercel.com{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, {"raw": body[:500]}


def main() -> int:
    print(f"→ target : {CLOUD_RUN}")
    print(f"→ domain : {DOMAIN}")

    # 1. Create (or reuse) the project
    status, body = api("POST", f"/v11/projects?teamId={TEAM_ID}", {"name": PROJECT, "framework": None})
    if status not in (200, 201):
        print(f"  project create: HTTP {status} {body.get('error', {}).get('code', body)}")
        status, body = api("GET", f"/v9/projects/{PROJECT}?teamId={TEAM_ID}")
        if status != 200:
            print("  FAIL: cannot create or read the project")
            return 1
    print(f"  project  : {body.get('name')} (id={body.get('id')})")

    # 2. Deploy the proxy
    status, body = api(
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
    if status not in (200, 201):
        print(f"  FAIL deploy: HTTP {status} {json.dumps(body)[:400]}")
        return 1
    print(f"  deploy   : {body.get('url')}  (state={body.get('readyState') or body.get('status')})")

    # 3. Attach the custom domain
    status, body = api("POST", f"/v10/projects/{PROJECT}/domains?teamId={TEAM_ID}", {"name": DOMAIN})
    if status in (200, 201):
        print("  domain   : attached")
    else:
        err = body.get("error", {})
        code = err.get("code")
        if code == "domain_already_in_use" or "already" in str(code):
            print("  domain   : already attached")
        else:
            print(f"  domain   : HTTP {status} {code or json.dumps(body)[:300]}")

    # 4. Report the DNS record the user must add
    status, cfg = api("GET", f"/v5/domains/{DOMAIN}/config?teamId={TEAM_ID}")
    print("\n=== DNS record to add at GoDaddy ===")
    print(f"  Type : CNAME")
    print(f"  Name : vidiforge")
    print(f"  Value: cname.vercel-dns.com")
    if status == 200:
        recs = cfg.get("recommendedCNAME") or []
        if recs:
            print(f"  (Vercel also accepts: {recs[0].get('value')})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
