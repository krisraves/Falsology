#!/usr/bin/env python3
"""Find distinct alternate YouTube uploads for every repeated exact statement."""

from __future__ import annotations

import concurrent.futures
import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "validation" / "alternate-upload-search.json"
INSTANCES = (
    "https://inv.nadeko.net",
    "https://invidious.nerdvpn.de",
    "https://invidious.tiekoetter.com",
)
USER_AGENT = "Mozilla/5.0 (compatible; FalsologyUniqueVideoSearch/1.0)"


def fetch_json(url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def search(query: str) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    encoded = urllib.parse.urlencode({"q": query, "type": "video", "sort_by": "relevance"})
    for instance in INSTANCES:
        try:
            value = fetch_json(f"{instance}/api/v1/search?{encoded}")
            if isinstance(value, list):
                videos = [item for item in value if isinstance(item, dict) and item.get("type") == "video"]
                return videos, errors
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{instance}: {type(exc).__name__}: {exc}")
    return [], errors


def main() -> int:
    exact = json.loads((ROOT / "data" / "exact-statement-overrides.json").read_text(encoding="utf-8"))
    by_video: dict[str, list[str]] = {}
    for case_number, item in exact.items():
        by_video.setdefault(item["media"]["youtubeId"], []).append(case_number)

    used_ids = {item["media"]["youtubeId"] for item in exact.values()}
    cases = [case for group in by_video.values() if len(group) > 1 for case in group[1:]]
    results: dict[str, Any] = {}

    def process(case_number: str) -> tuple[str, Any]:
        item = exact[case_number]
        query = f"{item['person']} {item['claim']}"
        videos, errors = search(query)
        candidates = []
        seen = set()
        for video in videos:
            video_id = str(video.get("videoId", ""))
            if len(video_id) != 11 or video_id in seen or video_id in used_ids:
                continue
            seen.add(video_id)
            candidates.append({
                "videoId": video_id,
                "title": video.get("title"),
                "author": video.get("author"),
                "lengthSeconds": video.get("lengthSeconds"),
                "viewCount": video.get("viewCount"),
                "publishedText": video.get("publishedText"),
            })
            if len(candidates) >= 12:
                break
        return case_number, {
            "person": item["person"],
            "claim": item["claim"],
            "currentVideoId": item["media"]["youtubeId"],
            "query": query,
            "candidates": candidates,
            "errors": errors,
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_map = {executor.submit(process, case): case for case in cases}
        for future in concurrent.futures.as_completed(future_map):
            case_number = future_map[future]
            try:
                key, result = future.result()
                results[key] = result
                print(f"{key}: {len(result['candidates'])} alternate candidates", flush=True)
            except Exception as exc:  # noqa: BLE001
                results[case_number] = {"error": f"{type(exc).__name__}: {exc}"}

    OUTPUT.write_text(json.dumps({"caseCount": len(cases), "cases": results}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
