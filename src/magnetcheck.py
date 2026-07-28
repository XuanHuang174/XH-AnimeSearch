from __future__ import annotations

import os

import httpx

MAGNETCHECK_BASE_URL = os.environ.get(
    "MAGNETCHECK_BASE_URL", "https://magnetcheck.nalanyinyun.work"
)
MAGNETCHECK_API_KEY = os.environ.get("MAGNETCHECK_API_KEY", "")
TIMEOUT = httpx.Timeout(30.0)


def check_health(magnet: str) -> httpx.Response:
    url = f"{MAGNETCHECK_BASE_URL.rstrip('/')}/health"
    headers = {"X-API-Key": MAGNETCHECK_API_KEY}
    with httpx.Client(timeout=TIMEOUT) as client:
        return client.get(url, headers=headers, params={"magnet": magnet})
