#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

VIDEO_ID = "3MuPWV5cTio"
VIDEO_URL = f"https://www.youtube.com/watch?v={VIDEO_ID}"
ENDPOINT = "https://youtube2text.diguardia.org/api/transcript"
HEADERS = {"user-agent": "Mozilla/5.0 Chrome/126 Safari/537.36"}
OUTPUT = Path("data/research/current-transcript-provider-probe.json")


def summarize_response(name: str, response: requests.Response) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": name,
        "status": response.status_code,
        "contentType": response.headers.get("content-type"),
        "length": len(response.content),
    }
    try:
        payload = response.json()
        result["jsonType"] = type(payload).__name__
        if isinstance(payload, dict):
            result["keys"] = list(payload.keys())[:20]
            for key in ("transcript", "segments", "captions", "data", "result"):
                value = payload.get(key)
                if isinstance(value, list):
                    result["listKey"] = key
                    result["listCount"] = len(value)
                    result["firstItem"] = value[0] if value else None
                    break
                if isinstance(value, dict):
                    result[f"{key}Keys"] = list(value.keys())[:20]
        elif isinstance(payload, list):
            result["listCount"] = len(payload)
            result["firstItem"] = payload[0] if payload else None
    except Exception:
        result["bodyPrefix"] = response.text[:500]
    return result


attempts = []
request_specs = [
    ("get-video-id", "get", {"params": {"video_id": VIDEO_ID}}),
    ("get-url", "get", {"params": {"url": VIDEO_URL}}),
    ("post-json-url", "post", {"json": {"url": VIDEO_URL}}),
    ("post-json-video-url", "post", {"json": {"video_url": VIDEO_URL}}),
    ("post-json-video-id", "post", {"json": {"video_id": VIDEO_ID}}),
    ("post-form-url", "post", {"data": {"url": VIDEO_URL}}),
]
for name, method, kwargs in request_specs:
    try:
        response = requests.request(method, ENDPOINT, headers=HEADERS, timeout=15, **kwargs)
        attempts.append(summarize_response(name, response))
    except Exception as exc:
        attempts.append({"name": name, "error": f"{type(exc).__name__}: {exc}"})

try:
    from youtube_transcript_api import YouTubeTranscriptApi

    try:
        fetched = YouTubeTranscriptApi().fetch(VIDEO_ID, languages=["en"])
        raw = fetched.to_raw_data() if hasattr(fetched, "to_raw_data") else list(fetched)
        attempts.append({
            "name": "youtube-transcript-api-fetch",
            "success": True,
            "count": len(raw),
            "firstItem": raw[0] if raw else None,
        })
    except Exception as first_error:
        try:
            raw = YouTubeTranscriptApi.get_transcript(VIDEO_ID, languages=["en"])
            attempts.append({
                "name": "youtube-transcript-api-get-transcript",
                "success": True,
                "count": len(raw),
                "firstItem": raw[0] if raw else None,
            })
        except Exception as second_error:
            attempts.append({
                "name": "youtube-transcript-api",
                "success": False,
                "errors": [f"{type(first_error).__name__}: {first_error}", f"{type(second_error).__name__}: {second_error}"],
            })
except Exception as exc:
    attempts.append({"name": "youtube-transcript-api-import", "error": f"{type(exc).__name__}: {exc}"})

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps({"videoId": VIDEO_ID, "attempts": attempts}, indent=2, default=str) + "\n")
print(json.dumps(attempts, indent=2, default=str))
