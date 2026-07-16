#!/usr/bin/env python3
"""Fetch timestamped transcripts for candidate replacement videos.

The output contains only keyword-relevant passages and enough surrounding context
to choose an exact direct quote and its ±15-second clip window.
"""

from __future__ import annotations

import concurrent.futures
import json
import random
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ENDPOINT = "https://youtube2text.diguardia.org/api/transcript"
OUTPUT = Path("validation/replacement-source-transcripts.json")
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
TIMEOUT = 90

CASES: dict[str, dict[str, Any]] = {
    "L06": {
        "person": "Ted Bundy",
        "keywords": ["innocent", "physically harmed", "mercy", "didnt do", "not guilty", "kill anyone"],
        "videos": ["AEWsxCrMM1U", "VO8hZ3Yy-sM", "CvGr3hMIS6A", "SmiiY1rQDVk"],
    },
    "L16": {
        "person": "Bill Clinton",
        "keywords": ["sexual relations", "miss lewinsky", "allegations are false", "never told anybody to lie"],
        "videos": ["VBe_guezGGc", "_aGbdni7QNs", "IYGBmV63Iow", "umj0gu5nEGs", "TM8EXwemnYA"],
    },
    "L17": {
        "person": "Kenneth Lay",
        "keywords": ["strongest", "best shape", "company is strong", "tremendous momentum", "fundamentally strong", "great shape"],
        "videos": ["S3EVIeZNHJU", "hwollZoVmUc", "Rjqgdggnlfo"],
    },
    "T03": {
        "person": "Edmund Kemper",
        "keywords": ["kill my mother", "killed my mother", "wanted to kill my mother", "murdered them", "my mother"],
        "videos": ["I8x5PeZZFNs", "ToXjwzwaq3Y"],
    },
    "T04": {
        "person": "Aileen Wuornos",
        "keywords": ["seven", "killed", "self defense", "i did everything", "confess", "shooting"],
        "videos": ["MKK3XDI7wTE", "3yi2dbaQ3mM", "KH1PCwyZOsY"],
    },
    "T08": {
        "person": "Alex Murdaugh",
        "keywords": ["kennel", "lied", "i was", "my voice", "paranoid", "not there"],
        "videos": ["xxjUDj82_h8", "XfbkJMVH0w0", "rEXrNoyv4Q8"],
    },
    "T15": {
        "person": "Mary Vincent",
        "keywords": ["arms", "cut", "hatchet", "survived", "threw me", "both"],
        "videos": ["TbJ_1vHagfQ", "CA-yk8-ALoc", "bphNcBD663M", "HhQmL2FKRDw", "UjV1cmesxdI", "W259o2tO2pc"],
    },
}


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def request_transcript(video_id: str) -> dict[str, Any]:
    body = json.dumps({"url": f"https://www.youtube.com/watch?v={video_id}", "lang": "en"}).encode()
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
    errors: list[str] = []
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                value = json.loads(response.read().decode("utf-8", errors="replace"))
            if not isinstance(value, dict) or not isinstance(value.get("segments"), list):
                raise RuntimeError("No timed segments returned")
            return value
        except Exception as exc:  # noqa: BLE001
            body_text = ""
            if isinstance(exc, urllib.error.HTTPError):
                try:
                    body_text = exc.read().decode("utf-8", errors="replace")[:600]
                except Exception:  # noqa: BLE001
                    pass
            errors.append(f"attempt {attempt + 1}: {type(exc).__name__}: {exc} {body_text}".strip())
            if attempt < 2:
                time.sleep(4 * (attempt + 1) + random.random())
    raise RuntimeError(" | ".join(errors))


def relevant_passages(segments: list[dict[str, Any]], keywords: list[str]) -> list[dict[str, Any]]:
    normalized_keywords = [normalize(keyword) for keyword in keywords]
    hits: list[dict[str, Any]] = []
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            continue
        text = str(segment.get("text", "")).strip()
        normalized = normalize(text)
        matched = [keyword for keyword, key in zip(keywords, normalized_keywords) if key and key in normalized]
        if not matched:
            # Also allow all content words from a short keyword phrase to appear in one segment.
            for keyword, key in zip(keywords, normalized_keywords):
                words = [word for word in key.split() if len(word) >= 3]
                if words and all(word in normalized.split() for word in words):
                    matched.append(keyword)
        if not matched:
            continue
        first = max(0, index - 3)
        last = min(len(segments), index + 4)
        context_rows = [row for row in segments[first:last] if isinstance(row, dict)]
        try:
            start = float(context_rows[0].get("start", 0.0))
            end = max(float(row.get("start", 0.0)) + float(row.get("duration", 0.0)) for row in context_rows)
            hit_start = float(segment.get("start", 0.0))
            hit_end = hit_start + float(segment.get("duration", 0.0))
        except (TypeError, ValueError):
            continue
        hits.append(
            {
                "matchedKeywords": matched,
                "hitStartSeconds": round(hit_start, 2),
                "hitEndSeconds": round(hit_end, 2),
                "hitText": text,
                "contextStartSeconds": round(start, 2),
                "contextEndSeconds": round(end, 2),
                "context": " ".join(str(row.get("text", "")).strip() for row in context_rows),
            }
        )
    # Deduplicate highly overlapping contexts.
    selected: list[dict[str, Any]] = []
    for hit in hits:
        if any(abs(hit["hitStartSeconds"] - existing["hitStartSeconds"]) < 1.0 for existing in selected):
            continue
        selected.append(hit)
        if len(selected) >= 20:
            break
    return selected


def main() -> int:
    tasks = [(case_number, config, video_id) for case_number, config in CASES.items() for video_id in config["videos"]]
    report: dict[str, Any] = {case_number: {"person": config["person"], "videos": {}} for case_number, config in CASES.items()}

    def fetch(task: tuple[str, dict[str, Any], str]) -> tuple[str, str, dict[str, Any]]:
        case_number, config, video_id = task
        value = request_transcript(video_id)
        segments = value.get("segments", [])
        result = {
            "segmentCount": len(segments),
            "textSample": str(value.get("text", ""))[:700],
            "passages": relevant_passages(segments, config["keywords"]),
        }
        return case_number, video_id, result

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        future_map = {executor.submit(fetch, task): task for task in tasks}
        for future in concurrent.futures.as_completed(future_map):
            case_number, _config, video_id = future_map[future]
            try:
                fetched_case, fetched_video, result = future.result()
                report[fetched_case]["videos"][fetched_video] = result
                print(f"{fetched_case} {fetched_video}: {len(result['passages'])} passage(s)", flush=True)
            except Exception as exc:  # noqa: BLE001
                report[case_number]["videos"][video_id] = {"error": f"{type(exc).__name__}: {exc}"}
                print(f"{case_number} {video_id}: FAILED", flush=True)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
