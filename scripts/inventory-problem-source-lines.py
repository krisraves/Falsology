#!/usr/bin/env python3
"""Inventory likely first-person/direct lines in cases whose original claim was absent.

This is a review aid, not an automatic production rewrite. It fetches timed
segments, ranks subject-relevant first-person passages, and includes enough
context to distinguish the named speaker from narration or an interviewer.
"""

from __future__ import annotations

import concurrent.futures
import importlib.util
import json
import os
import random
import re
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "scripts" / "audit-exact-statement-clips.py"
OUTPUT = ROOT / "validation" / "problem-source-line-inventory.md"
ENDPOINT = "https://youtube2text.diguardia.org/api/transcript"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
TIMEOUT = int(os.environ.get("INVENTORY_TIMEOUT", "65"))
WORKERS = int(os.environ.get("INVENTORY_WORKERS", "24"))

CASES = {
    "L02", "L04", "L05", "L07", "L09", "L10", "L11", "L14", "L19", "L20", "L25",
    "T01", "T02", "T05", "T06", "T07", "T09", "T10", "T11", "T13", "T14", "T18",
    "T19", "T20", "T22", "T23", "T24", "T25",
}

FIRST_PERSON = re.compile(r"\b(i|i'm|im|i've|ive|i'd|id|i'll|ill|me|my|mine|we|we're|were|we've|our|ours)\b", re.I)
QUESTION = re.compile(r"\b(did you|do you|are you|were you|can you|could you|would you|tell me|what did|why did|how did)\b", re.I)
STOP = {
    "about", "after", "again", "also", "and", "are", "because", "been", "before", "being", "but", "could",
    "does", "doing", "from", "have", "into", "just", "more", "most", "that", "their", "them", "then", "there",
    "these", "they", "this", "those", "through", "very", "what", "when", "where", "which", "with", "would", "your",
}


def load_audit() -> Any:
    spec = importlib.util.spec_from_file_location("falsology_audit", AUDIT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load case audit module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def normalize(text: str) -> list[str]:
    return [word for word in re.sub(r"[^a-z0-9]+", " ", text.lower()).split() if len(word) >= 3 and word not in STOP]


def fetch(video_id: str) -> list[dict[str, Any]]:
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
    time.sleep(random.uniform(0, 1.0))
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        value = json.loads(response.read().decode("utf-8", errors="replace"))
    segments = value.get("segments") if isinstance(value, dict) else None
    if not isinstance(segments, list) or not segments:
        raise RuntimeError("No timestamped segments returned")
    return [segment for segment in segments if isinstance(segment, dict)]


def passage(segments: list[dict[str, Any]], index: int, radius: int = 2) -> dict[str, Any] | None:
    first = max(0, index - radius)
    last = min(len(segments), index + radius + 1)
    rows = segments[first:last]
    try:
        start = float(segments[index].get("start", 0))
        duration = float(segments[index].get("duration", 0))
        context_start = float(rows[0].get("start", 0))
        context_end = max(float(row.get("start", 0)) + float(row.get("duration", 0)) for row in rows)
    except (TypeError, ValueError):
        return None
    return {
        "start": round(start, 2),
        "end": round(start + duration, 2),
        "contextStart": round(context_start, 2),
        "contextEnd": round(context_end, 2),
        "text": " ".join(str(segments[index].get("text", "")).split()),
        "context": " ".join(" ".join(str(row.get("text", "")).split()) for row in rows),
    }


def rank_lines(claim: dict[str, Any], segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    relevance = Counter(normalize(" ".join([
        str(claim.get("claim", "")), str(claim.get("context", "")), str(claim.get("fullTruth", "")),
        str(claim.get("classification", "")), str(claim.get("shortExplanation", "")),
    ])))
    candidates: list[dict[str, Any]] = []
    for index, segment in enumerate(segments):
        text = " ".join(str(segment.get("text", "")).split())
        if not FIRST_PERSON.search(text):
            continue
        words = Counter(normalize(text))
        overlap = sum((words & relevance).values())
        distinct = len(set(words) & set(relevance))
        score = overlap * 6 + distinct * 3 + min(4, len(words) / 5)
        if QUESTION.search(text):
            score -= 7
        if len(text) < 8:
            score -= 3
        item = passage(segments, index)
        if not item:
            continue
        item["score"] = round(score, 2)
        candidates.append(item)

    candidates.sort(key=lambda item: item["score"], reverse=True)
    selected: list[dict[str, Any]] = []
    for candidate in candidates:
        if any(abs(candidate["start"] - existing["start"]) < 4 for existing in selected):
            continue
        selected.append(candidate)
        if len(selected) >= 18:
            break
    return selected


def main() -> int:
    audit = load_audit()
    claims = {claim["caseNumber"]: claim for claim in audit.load_final_claims() if claim["caseNumber"] in CASES}
    results: dict[str, Any] = {}

    def process(item: tuple[str, dict[str, Any]]) -> tuple[str, dict[str, Any]]:
        case_number, claim = item
        video_id = str(claim["media"]["youtubeId"])
        segments = fetch(video_id)
        return case_number, {
            "person": claim["person"],
            "verdict": claim["verdict"],
            "original": claim["claim"],
            "videoId": video_id,
            "duration": claim["media"]["videoDurationSeconds"],
            "lines": rank_lines(claim, segments),
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(WORKERS, len(claims))) as executor:
        future_map = {executor.submit(process, item): item[0] for item in claims.items()}
        for future in concurrent.futures.as_completed(future_map):
            case_number = future_map[future]
            try:
                fetched_case, result = future.result()
                results[fetched_case] = result
                print(f"{fetched_case}: {len(result['lines'])} candidate line(s)", flush=True)
            except Exception as exc:  # noqa: BLE001
                results[case_number] = {"error": f"{type(exc).__name__}: {exc}"}
                print(f"{case_number}: FAILED", flush=True)

    lines = ["# Problem Source Direct-Line Inventory", ""]
    for case_number in sorted(CASES):
        result = results.get(case_number, {"error": "Missing result"})
        lines.append(f"## {case_number} — {result.get('person', '')}")
        if result.get("error"):
            lines.append(f"**ERROR:** {result['error']}")
            lines.append("")
            continue
        lines.append(f"**Original:** {result['original']}")
        lines.append(f"**Video:** `{result['videoId']}` · {result['duration']}s")
        for index, item in enumerate(result["lines"], start=1):
            lines.append(f"{index}. **{item['start']}–{item['end']}s** score {item['score']} — “{item['text']}”")
            lines.append(f"   Context {item['contextStart']}–{item['contextEnd']}s: {item['context']}")
        lines.append("")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
