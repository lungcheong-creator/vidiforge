#!/usr/bin/env python3
"""Submit a Cloud Build job that builds and pushes the VidiForge image.

Needed because `gcloud builds submit` performs a client-side
`iam.serviceAccounts.get` check that this service account cannot satisfy; the
REST API accepts an explicitly named service account.

Usage:  python3 cloudbuild_submit.py <tag> <gcs-object>
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

PROJECT = "vidiforge-deployer"
REGION = "asia-east1"
BUCKET = "vidiforge-deployer_cloudbuild"


def access_token() -> str:
    out = subprocess.run(
        ["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    tag, gcs_object = sys.argv[1], sys.argv[2]
    image = f"{REGION}-docker.pkg.dev/{PROJECT}/vidiforge/vidiforge:{tag}"

    payload = {
        "source": {"storageSource": {"bucket": BUCKET, "object": gcs_object}},
        "serviceAccount": (
            f"projects/{PROJECT}/serviceAccounts/"
            f"vidiforge-deployer@{PROJECT}.iam.gserviceaccount.com"
        ),
        "logsBucket": f"gs://{BUCKET}/logs",
        "steps": [
            {
                "name": "gcr.io/cloud-builders/docker",
                "id": "build",
                "args": ["build", "-f", "Dockerfile", "-t", image, "."],
            },
            {
                "name": "gcr.io/cloud-builders/docker",
                "id": "push",
                "args": ["push", image],
            },
        ],
        "images": [image],
        "options": {"machineType": "E2_HIGHCPU_8", "diskSizeGb": 50, "logging": "LEGACY"},
        "timeout": "1800s",
    }

    req = urllib.request.Request(
        f"https://cloudbuild.googleapis.com/v1/projects/{PROJECT}/builds",
        data=json.dumps(payload).encode(),
        method="POST",
    )
    req.add_header("Authorization", f"Bearer {access_token()}")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            body = json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()[:400]}")
        return 1

    build = body.get("metadata", {}).get("build", {})
    print(f"image    : {image}")
    print(f"build id : {build.get('id')}")
    print(f"status   : {build.get('status')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
