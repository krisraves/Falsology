#!/usr/bin/env python3
"""Probe caption mirrors with one known-caption video."""

from __future__ import annotations

import concurrent.futures
import json
import urllib.parse
import urllib.request

VIDEO_ID = "3MuPWV5cTio"
TIMEOUT = 5
USER_AGENT = "Mozilla/5.0 (compatible; FalsologyTimestampProbe/1.0)"

INVIDIOUS = (
    "https://inv.nadeko.net",
    "https://invidious.nerdvpn.de",
    "https://yt.chocolatemoo53.com",
    "https://invidious.tiekoetter.com",
    "https://invidious.f5.si",
    "https://inv.zoomerville.com",
)
PIPED = (
    "https://pipedapi.adminforge.de",
    "https://pipedapi.reallyaweso.me",
    "https://pipedapi.kavin.rocks",
    "https://pipedapi-libre.kavin.rocks",
)


def request(url: str) -> tuple[int, str, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return response.status, response.headers.get("Content-Type", ""), response.read(2000)


def probe(kind: str, instance: str) -> dict[str, object]:
    if kind == "invidious":
        url = f"{instance}/api/v1/captions/{urllib.parse.quote(VIDEO_ID)}?lang=en"
    else:
        url = f"{instance}/streams/{urllib.parse.quote(VIDEO_ID)}"
    try:
        status, content_type, payload = request(url)
        text = payload.decode("utf-8", errors="replace")
        usable = "WEBVTT" in text[:100].upper()
        if kind == "piped" and "json" in content_type.lower():
            value = json.loads(text)
            tracks = value.get("subtitles") or value.get("captions") or []
            usable = any(
                isinstance(track, dict)
                and str(track.get("code") or track.get("languageCode") or track.get("label") or "").lower().startswith("en")
                and bool(track.get("url"))
                for track in tracks
            )
        return {
            "kind": kind,
            "instance": instance,
            "status": status,
            "contentType": content_type,
            "usable": usable,
            "sample": text[:160].replace("\n", " "),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "kind": kind,
            "instance": instance,
            "usable": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> int:
    providers = [
        *(("invidious", instance) for instance in INVIDIOUS),
        *(("piped", instance) for instance in PIPED),
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(providers)) as executor:
        results = list(executor.map(lambda item: probe(*item), providers))
    print(json.dumps(results, indent=2))
    usable = [result for result in results if result.get("usable")]
    print(f"USABLE_PROVIDERS={len(usable)}")
    for result in usable:
        print(f"USABLE={result['kind']} {result['instance']}")
    return 0 if usable else 1


if __name__ == "__main__":
    raise SystemExit(main())
