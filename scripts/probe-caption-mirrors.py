#!/usr/bin/env python3
"""Inspect caption-track responses from the reachable Invidious mirror."""

from __future__ import annotations

import concurrent.futures
import json
import urllib.parse
import urllib.request
from pathlib import Path

VIDEO_ID = "3MuPWV5cTio"
TIMEOUT = 12
USER_AGENT = "Mozilla/5.0 (compatible; FalsologyTimestampProbe/1.0)"
OUTPUT = Path("validation/caption-provider-probe.json")
INSTANCE = "https://inv.nadeko.net"

QUERIES = (
    "",
    "?lang=en",
    "?lang=en-US",
    "?lang=en-GB",
    "?label=English",
    "?label=English%20(auto-generated)",
)


def request(url: str) -> tuple[int, str, bytes]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/vtt, application/json;q=0.9, */*;q=0.5",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return response.status, response.headers.get("Content-Type", ""), response.read(20000)


def probe(query: str) -> dict[str, object]:
    base = f"{INSTANCE}/api/v1/captions/{urllib.parse.quote(VIDEO_ID)}"
    url = base + query
    try:
        status, content_type, payload = request(url)
        text = payload.decode("utf-8", errors="replace")
        return {
            "query": query or "(track index)",
            "url": url,
            "status": status,
            "contentType": content_type,
            "byteLength": len(payload),
            "hasWebVtt": "WEBVTT" in text[:100].upper(),
            "sample": text[:4000],
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "query": query or "(track index)",
            "url": url,
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> int:
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(QUERIES)) as executor:
        results = list(executor.map(probe, QUERIES))
    report = {"videoId": VIDEO_ID, "instance": INSTANCE, "results": results}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
