"""
Public endpoints smoke checks (no auth) to "prove data can be retrieved" from DEX.

These are intentionally minimal and may need adjustment if a DEX changes endpoints.
"""
from __future__ import annotations

from dataclasses import dataclass

import requests

UA = "dex-auth-automation/0.1 (+https://example.local)"


@dataclass(frozen=True)
class PublicResult:
    ok: bool
    status_code: int
    url: str
    payload_preview: str


def lighter_public_info(base_url: str) -> PublicResult:
    url = base_url.rstrip("/") + "/info"
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
        preview = r.text[:500]
        return PublicResult(ok=r.ok, status_code=r.status_code, url=url, payload_preview=preview)
    except requests.RequestException as e:
        return PublicResult(ok=False, status_code=0, url=url, payload_preview=str(e))


def hyperliquid_public_meta(api_url: str) -> PublicResult:
    # Official ecosystem commonly uses POST /info with {"type":"meta"} on https://api.hyperliquid.xyz
    url = api_url.rstrip("/") + "/info"
    try:
        r = requests.post(url, json={"type": "meta"}, headers={"User-Agent": UA}, timeout=20)
        preview = r.text[:500]
        return PublicResult(ok=r.ok, status_code=r.status_code, url=url, payload_preview=preview)
    except requests.RequestException as e:
        return PublicResult(ok=False, status_code=0, url=url, payload_preview=str(e))


def standx_public_health(base_url: str) -> PublicResult:
    # StandX health check
    url = base_url.rstrip("/") + "/health"
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
        preview = r.text[:500]
        return PublicResult(ok=r.ok, status_code=r.status_code, url=url, payload_preview=preview)
    except requests.RequestException as e:
        return PublicResult(ok=False, status_code=0, url=url, payload_preview=str(e))


def grvt_public_health(base_url: str) -> PublicResult:
    # GRVT health check
    # Many endpoints return 403; we return result regardless to show "reachability" vs "timeout".
    url = base_url.rstrip("/") + "/health"  # Try root health or similar
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=10)
        preview = r.text[:500]
        # Even 403 is a "success" in terms of "server exists and responded" vs ConnectionError
        return PublicResult(ok=r.ok, status_code=r.status_code, url=url, payload_preview=preview)
    except requests.RequestException as e:
        return PublicResult(ok=False, status_code=0, url=url, payload_preview=str(e))
