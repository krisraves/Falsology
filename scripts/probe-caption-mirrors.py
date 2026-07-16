#!/usr/bin/env python3
"""Test the hosted transcript endpoint against a Falsology source."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

OUTPUT = Path("validation/caption-provider-probe.json")
ENDPOINT = "https://youtube2text.diguardia.org/api/transcript"
VIDEO_ID = "3MuPWV5cTio"
VIDEO_URL = f"https://www.youtube.com/watch?v={VIDEO_ID}"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"


def main() -> int:
    body = json.dumps({"url": VIDEO_URL, "lang": "en"}).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": "https://youtube2text.diguardia.org",
            "Referer": "https://youtube2text.diguardia.org/",
        },
    )
    report: dict[str, object] = {"endpoint": ENDPOINT, "videoId": VIDEO_ID}
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = response.read()
            report["status"] = response.status
            report["contentType"] = response.headers.get("Content-Type", "")
            report["byteLength"] = len(payload)
            value = json.loads(payload.decode("utf-8", errors="replace"))
            segments = value.get("segments") if isinstance(value, dict) else None
            report["keys"] = list(value.keys()) if isinstance(value, dict) else []
            report["segmentCount"] = len(segments) if isinstance(segments, list) else None
            report["firstSegments"] = segments[:20] if isinstance(segments, list) else None
            report["textSample"] = str(value.get("text", ""))[:2000] if isinstance(value, dict) else str(value)[:2000]
    except Exception as exc:  # noqa: BLE001
        report["error"] = f"{type(exc).__name__}: {exc}"
        if hasattr(exc, "read"):
            try:
                report["errorBody"] = exc.read().decode("utf-8", errors="replace")[:4000]
            except Exception:  # noqa: BLE001
                pass

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
