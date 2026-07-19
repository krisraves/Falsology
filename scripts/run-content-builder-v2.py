#!/usr/bin/env python3
"""Run the content builder with confirmed embed and timed-caption providers."""

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
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        response = requests.get(oembed_url, headers=module.HEADERS, timeout=20)
        if response.status_code != 200:
            return None
        data = response.json()
        embed_response = requests.get(
            f"https://www.youtube.com/embed/{video_id}?hl=en",
            headers=module.HEADERS,
            timeout=20,
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
    try:
        response = requests.post(
            module.TRANSCRIPT_ENDPOINT,
            json={"url": video_url},
            headers=module.HEADERS,
            timeout=30,
        )
        if response.status_code == 200:
            segments = parse_segments(response.json())
            if segments:
                return segments
    except Exception:
        pass

    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        fetched = YouTubeTranscriptApi().fetch(video_id, languages=["en"])
        raw_values = fetched.to_raw_data() if hasattr(fetched, "to_raw_data") else list(fetched)
        return parse_segments(raw_values)
    except Exception:
        return []


def efficient_process_seed(seed: dict[str, Any]) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    accepted: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    rejection_counts: dict[str, int] = {
        "duplicateSearchResult": 0,
        "failedVerification": 0,
    }
    for query in list(seed.get("searchQueries") or [])[:2]:
        search_results = module.youtube_search(str(query))
        attempts.append({"query": query, "resultCount": len(search_results)})
        for candidate in search_results[:8]:
            video_id = candidate["videoId"]
            if video_id in seen_ids:
                rejection_counts["duplicateSearchResult"] += 1
                continue
            seen_ids.add(video_id)
            evaluated = module.evaluate_video(seed, candidate)
            if evaluated:
                accepted.append(evaluated)
                accepted.sort(key=lambda item: item["confidence"], reverse=True)
                accepted = accepted[:2]
                if len(accepted) >= 2:
                    break
            else:
                rejection_counts["failedVerification"] += 1
        if accepted:
            break
    return {
        "seed": seed,
        "attempts": attempts,
        "candidates": accepted,
        "rejectionCounts": rejection_counts,
    }


module.youtube_public_metadata = youtube_public_metadata
module.timed_transcript = provider_transcript
module.process_seed = efficient_process_seed
module.SEARCH_WORKERS = 8
exit_code = module.main()

if module.REPORT_PATH.exists():
    report = json.loads(module.REPORT_PATH.read_text(encoding="utf-8"))
    report["methodVersion"] = 4
    report["embedCheck"] = "YouTube oEmbed plus reachable embed endpoint"
    report["transcriptProviders"] = [
        "Confirmed YouTube2Text POST {url} timed segments",
        "youtube-transcript-api timed caption fallback",
    ]
    report["candidateEvaluationLimit"] = "Eight search results per query; stop after two verified options"
    module.REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

raise SystemExit(exit_code)
