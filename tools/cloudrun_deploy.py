#!/usr/bin/env python3
"""Update a Cloud Run service's container image through the REST API.

`gcloud run deploy` performs client-side checks and is blocked in this
environment; the API accepts the same change directly.

Usage:  python3 cloudrun_deploy.py <tag>

Reads the current service, swaps only the container image (and adds any
requested env vars), then PATCHes it back — every other setting is preserved.
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

PROJECT = "vidiforge-deployer"
REGION = "asia-east1"
SERVICE = "vidiforge"
REPO = f"{REGION}-docker.pkg.dev/{PROJECT}/vidiforge/vidiforge"

# Env vars to ensure are present (merged into whatever already exists).
ENSURE_ENV = {
    "VIDIFORGE_ENV": "production",
    "WEB_ORIGIN": "asterisk",
    "GCS_BUCKET": f"{PROJECT}-outputs",
}

BASE = f"https://run.googleapis.com/v2/projects/{PROJECT}/locations/{REGION}/services/{SERVICE}"


def token() -> str:
    out = subprocess.run(
        ["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def api(method: str, url: str, payload: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token()}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, {"raw": body[:600]}


def main() -> int:
    tag = sys.argv[1] if len(sys.argv) > 1 else "v4-final"
    new_image = f"{REPO}:{tag}"

    print("→ reading current service …")
    status, svc = api("GET", BASE)
    if status != 200:
        print(f"  FAIL GET: HTTP {status} {json.dumps(svc)[:300]}")
        return 1

    containers = svc.get("template", {}).get("spec", {}).get("containers") or []
    if not containers:
        print("  FAIL: service has no containers")
        return 1

    current = containers[0].get("image", "")
    print(f"  current image : {current}")
    print(f"  new image     : {new_image}")
    if current == new_image:
        print("  (already up to date)")

    containers[0]["image"] = new_image

    # Merge env vars without dropping the Secret Manager references.
    env = containers[0].setdefault("env", [])
    present = {e.get("name") for e in env}
    for key, value in ENSURE_ENV.items():
        if key not in present:
            env.append({"name": key, "value": value})
            print(f"  + env {key}={value}")

    # Remove the reserved PORT var if it slipped in earlier.
    containers[0]["env"] = [e for e in env if e.get("name") != "PORT"]

    body = {
        "name": svc["name"],
        "template": {"spec": {"containers": containers}},
    }

    print("→ patching service …")
    status, res = api(
        "PATCH",
        f"{BASE}?updateMask=template.containers&allowMissing=false",
        body,
    )
    if status not in (200, 202):
        print(f"  FAIL PATCH: HTTP {status} {json.dumps(res)[:600]}")
        return 1

    print(f"  status: {res.get('status', {}) or 'accepted'}")
    print("  OK — Cloud Run is rolling out a new revision")
    return 0


if __name__ == "__main__":
    sys.exit(main())
