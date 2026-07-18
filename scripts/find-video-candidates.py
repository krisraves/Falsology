#!/usr/bin/env python3
"""Find 100 unique YouTube candidates for each Falsology difficulty.

This produces an editorial research pool, not automatically published game
content. Every candidate must still receive statement-level timestamp, verdict,
and source review before activation.
"""

from __future__ import annotations

import concurrent.futures
import json
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
QUERY_PATH = ROOT / "data" / "video-research-queries.json"
OUTPUT_PATH = ROOT / "data" / "research" / "video-candidates.json"
TARGET_PER_LEVEL = 100
RESULTS_PER_QUERY = 4
WORKERS = 8

REJECT_TITLE_TERMS = (
    "reaction",
    "explained",
    "analysis",
    "body language",
    "compilation",
    "top 10",
    "shorts",
    "#shorts",
    "podcast reacts",
)

DIRECT_TITLE_TERMS = (
    "interview",
    "interrogation",
    "testimony",
    "hearing",
    "statement",
    "speech",
    "confession",
    "deposition",
    "press conference",
    "court",
    "trial",
    "full",
    "raw",
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def existing_video_ids() -> set[str]:
    path = ROOT / "data" / "exact-statement-overrides.json"
    if not path.exists():
        return set()
    data = read_json(path)
    return {
        str(item.get("media", {}).get("youtubeId", ""))
        for item in data.values()
        if item.get("media", {}).get("youtubeId")
    }


def search(query: str) -> tuple[str, list[dict[str, Any]], str | None]:
    command = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        "--no-warnings",
        "--ignore-errors",
        f"ytsearch{RESULTS_PER_QUERY}:{query}",
    ]
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        return query, [], "Search timed out"

    items: list[dict[str, Any]] = []
    for line in result.stdout.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        video_id = str(value.get("id", ""))
        title = str(value.get("title", "")).strip()
        if len(video_id) != 11 or not title:
            continue
        items.append(
            {
                "videoId": video_id,
                "title": title,
                "channel": value.get("channel") or value.get("uploader") or "Unknown channel",
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "searchQuery": query,
            }
        )
    error = None if items else (result.stderr.strip()[-500:] or "No candidates returned")
    return query, items, error


def candidate_score(item: dict[str, Any]) -> int:
    title = str(item["title"]).lower()
    score = 0
    score += sum(3 for term in DIRECT_TITLE_TERMS if term in title)
    score -= sum(8 for term in REJECT_TITLE_TERMS if term in title)
    if "news" in title and not any(term in title for term in ("interview", "statement", "testimony", "full")):
        score -= 3
    return score


def main() -> int:
    queries = read_json(QUERY_PATH)
    existing = existing_video_ids()
    used = set(existing)
    final: dict[str, list[dict[str, Any]]] = {"easy": [], "hard": [], "expert": []}
    errors: dict[str, list[dict[str, str]]] = defaultdict(list)

    jobs: list[tuple[str, str]] = []
    for difficulty in ("easy", "hard", "expert"):
        for query in queries[difficulty]:
            jobs.append((difficulty, str(query)))

    results: dict[tuple[str, str], list[dict[str, Any]]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
        future_map = {executor.submit(search, query): (difficulty, query) for difficulty, query in jobs}
        for completed, future in enumerate(concurrent.futures.as_completed(future_map), start=1):
            difficulty, query = future_map[future]
            try:
                _, items, error = future.result()
                results[(difficulty, query)] = items
                if error:
                    errors[difficulty].append({"query": query, "error": error})
            except Exception as exc:  # noqa: BLE001
                results[(difficulty, query)] = []
                errors[difficulty].append({"query": query, "error": f"{type(exc).__name__}: {exc}"})
            print(f"[{completed}/{len(jobs)}] {difficulty}: {query}", flush=True)

    for difficulty in ("easy", "hard", "expert"):
        ranked: list[dict[str, Any]] = []
        for query in queries[difficulty]:
            for item in results.get((difficulty, str(query)), []):
                ranked.append({**item, "candidateScore": candidate_score(item)})
        ranked.sort(key=lambda item: item["candidateScore"], reverse=True)

        for item in ranked:
            video_id = item["videoId"]
            if video_id in used:
                continue
            used.add(video_id)
            final[difficulty].append(
                {
                    **item,
                    "difficulty": difficulty,
                    "reviewStatus": "candidate",
                    "directFootageLikely": item["candidateScore"] > 0,
                    "requiredReview": [
                        "Confirm the named person speaks directly",
                        "Identify the exact statement and timestamps",
                        "Verify truth or lie using primary and secondary evidence",
                        "Set a clip from 15 seconds before through 15 seconds after the statement",
                    ],
                }
            )
            if len(final[difficulty]) >= TARGET_PER_LEVEL:
                break

    report = {
        "generatedAt": "2026-07-18",
        "status": "editorial-research-pool",
        "notice": "Candidates are not playable until statement, verdict, timestamps, and sources are verified.",
        "targetPerDifficulty": TARGET_PER_LEVEL,
        "counts": {difficulty: len(items) for difficulty, items in final.items()},
        "totalUniqueCandidates": sum(len(items) for items in final.values()),
        "candidates": final,
        "searchErrors": errors,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    incomplete = {difficulty: count for difficulty, count in report["counts"].items() if count < TARGET_PER_LEVEL}
    if incomplete:
        print(f"Candidate discovery incomplete: {incomplete}", flush=True)
        return 2

    print("Found 300 unique candidate videos: 100 easy, 100 hard, 100 expert.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
