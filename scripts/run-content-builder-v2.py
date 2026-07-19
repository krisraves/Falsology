#!/usr/bin/env python3
"""Run the content builder with reliable embed and timed-caption providers."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import requests

SCRIPT = Path(__file__).with_name("build-verified-content-deck.py")
spec = importlib.util.spec_from_file_location("falsology_content_builder", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load content builder")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def youtube_public_metadata(video_id: str) -> dict[str, Any] | None:
    """Confirm a public YouTube watch page without scanning generic UI strings."""
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        response = requests.get(oembed_url, headers=module.HEADERS, timeout=module.HTTP_TIMEOUT)
        if response.status_code != 200:
            return None
        data = response.json()
        embed_response = requests.get(
            f"https://www.youtube.com/embed/{video_id}?hl=en",
            headers=module.HEADERS,
            timeout=module.HTTP_TIMEOUT,
        )
        if embed_response.status_code >= 400:
            return None
        return {
            "title": str(data.get("title") or ""),
            "channel": str(data.get("author_name") or "YouTube source channel"),
            "embeddable": True,
        }
    except Exception:
        return None


def parse_segments(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        for key in ("transcript", "segments", "captions", "data", "result"):
            if key in payload:
                nested = payload[key]
                if isinstance(nested, dict):
                    for nested_key in ("transcript", "segments", "captions", "data"):
                        if nested_key in nested:
                            nested = nested[nested_key]
                            break
                payload = nested
                break
    if not isinstance(payload, list):
        return []
    output: list[dict[str, Any]] = []
    for raw in payload:
        if not isinstance(raw, dict):
            continue
        text = str(raw.get("text") or raw.get("content") or raw.get("utf8") or raw.get("caption") or "").strip()
        start = raw.get("start")
        if start is None:
            start = raw.get("offset")
        if start is None and raw.get("startMs") is not None:
            start = float(raw["startMs"]) / 1000
        duration = raw.get("duration")
        end = raw.get("end")
        if duration is None and raw.get("durationMs") is not None:
            duration = float(raw["durationMs"]) / 1000
        try:
            start_number = float(start)
            if duration is not None:
                duration_number = max(0.05, float(duration))
            elif end is not None:
                duration_number = max(0.05, float(end) - start_number)
            else:
                duration_number = 0.5
        except (TypeError, ValueError):
            continue
        if text:
            output.append({"text": text, "start": start_number, "duration": duration_number})
    output.sort(key=lambda item: item["start"])
    return output


def provider_transcript(video_id: str) -> list[dict[str, Any]]:
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    endpoint = module.TRANSCRIPT_ENDPOINT
    attempts = [
        ("post-json-url", lambda: requests.post(endpoint, json={"url": video_url}, headers=module.HEADERS, timeout=55)),
        ("post-json-video", lambda: requests.post(endpoint, json={"video_url": video_url}, headers=module.HEADERS, timeout=55)),
        ("post-form-url", lambda: requests.post(endpoint, data={"url": video_url}, headers=module.HEADERS, timeout=55)),
        ("get-url", lambda: requests.get(endpoint, params={"url": video_url}, headers=module.HEADERS, timeout=55)),
        ("get-video-id", lambda: requests.get(endpoint, params={"video_id": video_id}, headers=module.HEADERS, timeout=55)),
    ]
    for _, request in attempts:
        try:
            response = request()
            if response.status_code != 200:
                continue
            segments = parse_segments(response.json())
            if segments:
                return segments
        except Exception:
            continue

    # Independent fallback for YouTube's public caption tracks.
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        try:
            fetched = YouTubeTranscriptApi().fetch(video_id, languages=["en"])
            raw_values = fetched.to_raw_data() if hasattr(fetched, "to_raw_data") else list(fetched)
        except Exception:
            raw_values = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
        segments = parse_segments(raw_values)
        if segments:
            return segments
    except Exception:
        pass
    return []


module.youtube_public_metadata = youtube_public_metadata
module.timed_transcript = provider_transcript
exit_code = module.main()

if module.REPORT_PATH.exists():
    report = json.loads(module.REPORT_PATH.read_text(encoding="utf-8"))
    report["methodVersion"] = 3
    report["embedCheck"] = "YouTube oEmbed plus reachable embed endpoint"
    report["transcriptProviders"] = [
        "YouTube2Text URL-based POST and GET variants",
        "youtube-transcript-api timed caption fallback",
    ]
    module.REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

raise SystemExit(exit_code)
