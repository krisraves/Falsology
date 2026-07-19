#!/usr/bin/env python3
"""Efficient verified-content build using the confirmed timed-caption API."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import requests

SCRIPT = Path(__file__).with_name("build-verified-content-deck.py")
spec = importlib.util.spec_from_file_location("falsology_content_builder_v5", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load content builder")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def parse_segments(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        payload = payload.get("segments") or payload.get("transcript") or payload.get("data") or payload.get("result") or []
        if isinstance(payload, dict):
            payload = payload.get("segments") or payload.get("transcript") or payload.get("data") or []
    if not isinstance(payload, list):
        return []
    output: list[dict[str, Any]] = []
    for raw in payload:
        if not isinstance(raw, dict):
            continue
        text = str(raw.get("text") or raw.get("content") or raw.get("utf8") or "").strip()
        start = raw.get("start")
        duration = raw.get("duration")
        end = raw.get("end")
        try:
            start_number = float(start)
            duration_number = max(0.05, float(duration)) if duration is not None else max(0.05, float(end) - start_number)
        except (TypeError, ValueError):
            continue
        if text:
            output.append({"text": text, "start": start_number, "duration": duration_number})
    output.sort(key=lambda item: item["start"])
    return output


def timed_transcript(video_id: str) -> list[dict[str, Any]]:
    try:
        response = requests.post(
            module.TRANSCRIPT_ENDPOINT,
            json={"url": f"https://www.youtube.com/watch?v={video_id}"},
            headers=module.HEADERS,
            timeout=22,
        )
        if response.status_code == 200:
            return parse_segments(response.json())
    except Exception:
        pass
    return []


def public_metadata(video_id: str) -> dict[str, Any] | None:
    try:
        response = requests.get(
            f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json",
            headers=module.HEADERS,
            timeout=15,
        )
        if response.status_code != 200:
            return None
        data = response.json()
        return {
            "title": str(data.get("title") or ""),
            "channel": str(data.get("author_name") or "YouTube source channel"),
            "embeddable": True,
        }
    except Exception:
        return None


def efficient_process_seed(seed: dict[str, Any]) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    checked = 0
    for query in list(seed.get("searchQueries") or [])[:2]:
        search_results = module.youtube_search(str(query))
        attempts.append({"query": query, "resultCount": len(search_results)})
        for candidate in search_results[:4]:
            if candidate["videoId"] in seen_ids:
                continue
            seen_ids.add(candidate["videoId"])
            checked += 1
            evaluated = module.evaluate_video(seed, candidate)
            if evaluated:
                return {
                    "seed": seed,
                    "attempts": attempts,
                    "candidates": [evaluated],
                    "checkedCandidates": checked,
                }
    return {
        "seed": seed,
        "attempts": attempts,
        "candidates": [],
        "checkedCandidates": checked,
    }


module.timed_transcript = timed_transcript
module.youtube_public_metadata = public_metadata
module.process_seed = efficient_process_seed
module.SEARCH_WORKERS = 12
exit_code = module.main()

if module.REPORT_PATH.exists():
    report = json.loads(module.REPORT_PATH.read_text(encoding="utf-8"))
    report["methodVersion"] = 5
    report["transcriptProvider"] = "Confirmed YouTube2Text POST {url} timed segments"
    report["candidateEvaluationLimit"] = "Top four results per query; one verified source per seed"
    module.REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

raise SystemExit(exit_code)
