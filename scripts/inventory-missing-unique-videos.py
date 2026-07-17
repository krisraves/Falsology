#!/usr/bin/env python3
"""Fetch exact first-person passages for unique videos missing prior matches."""

from __future__ import annotations

import concurrent.futures
import json
import random
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "https://youtube2text.diguardia.org/api/transcript"
OUTPUT = ROOT / "validation" / "missing-unique-video-lines.json"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
TIMEOUT = 120
ATTEMPTS = 4
WORKERS = 2

FIRST_PERSON = re.compile(r"\b(i|i'm|im|i've|ive|i'd|id|i'll|ill|me|my|mine|we|we're|were|we've|our|ours)\b", re.I)
QUESTION = re.compile(r"\b(did you|do you|are you|were you|can you|could you|would you|tell me|what did|why did|how did)\b", re.I)
STOP = {
    "about", "after", "again", "also", "and", "are", "because", "been", "before", "being", "but", "could",
    "does", "doing", "from", "have", "into", "just", "more", "most", "that", "their", "them", "then", "there",
    "these", "they", "this", "those", "through", "very", "what", "when", "where", "which", "with", "would", "your",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(text: str) -> list[str]:
    return [word for word in re.sub(r"[^a-z0-9]+", " ", text.lower()).split() if len(word) >= 3 and word not in STOP]


def load_pre_exact() -> dict[str, dict[str, Any]]:
    base = []
    for path in sorted((ROOT / "data" / "cases").glob("part??.json")):
        base.extend(read_json(path))
    layers = [
        read_json(ROOT / "data" / "case-overrides.json"),
        read_json(ROOT / "data" / "direct-footage-replacements.json"),
        read_json(ROOT / "data" / "obscure-case-replacements.json"),
        read_json(ROOT / "data" / "english-weird-replacements.json"),
    ]
    result = {}
    for item in base:
        claim = item
        for layer in layers:
            override = layer.get(item["caseNumber"], {})
            claim = {**claim, **override, "media": {**claim.get("media", {}), **override.get("media", {})}}
        result[item["caseNumber"]] = claim
    return result


def fetch(video_id: str) -> list[dict[str, Any]]:
    body = json.dumps({"url": f"https://www.youtube.com/watch?v={video_id}", "lang": "en"}).encode()
    errors = []
    for attempt in range(1, ATTEMPTS + 1):
        req = urllib.request.Request(
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
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                value = json.loads(response.read().decode("utf-8", errors="replace"))
            segments = value.get("segments") if isinstance(value, dict) else None
            if not isinstance(segments, list) or not segments:
                raise RuntimeError("No timed transcript segments returned")
            return [segment for segment in segments if isinstance(segment, dict)]
        except Exception as exc:  # noqa: BLE001
            detail = ""
            if isinstance(exc, urllib.error.HTTPError):
                try:
                    detail = exc.read().decode("utf-8", errors="replace")[:500]
                except Exception:  # noqa: BLE001
                    pass
            errors.append(f"attempt {attempt}: {type(exc).__name__}: {exc} {detail}".strip())
            if attempt < ATTEMPTS:
                time.sleep(attempt * 10 + random.uniform(1, 4))
    raise RuntimeError(" | ".join(errors))


def parsed(segment: dict[str, Any]) -> tuple[float, float, str] | None:
    text = " ".join(str(segment.get("text", "")).split())
    try:
        start = float(segment.get("start", 0))
        duration = float(segment.get("duration", 0))
    except (TypeError, ValueError):
        return None
    if not text or duration <= 0:
        return None
    return start, start + duration, text


def rank(claim: dict[str, Any], segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    relevance = Counter(normalize(" ".join([
        str(claim.get("claim", "")), str(claim.get("transcript", "")), str(claim.get("context", "")),
        str(claim.get("fullTruth", "")), str(claim.get("shortExplanation", "")), str(claim.get("classification", "")),
    ])))
    candidates = []
    for index, segment in enumerate(segments):
        value = parsed(segment)
        if not value:
            continue
        start, end, text = value
        if not FIRST_PERSON.search(text):
            continue
        words = Counter(normalize(text))
        overlap = sum((words & relevance).values())
        distinct = len(set(words) & set(relevance))
        score = overlap * 8 + distinct * 4 + min(5, len(words) / 4)
        if QUESTION.search(text):
            score -= 10
        first = max(0, index - 3)
        last = min(len(segments), index + 4)
        rows = [parsed(row) for row in segments[first:last]]
        rows = [row for row in rows if row]
        context = " ".join(row[2] for row in rows)
        candidates.append({
            "score": round(score, 2),
            "startSeconds": round(start, 2),
            "endSeconds": round(end, 2),
            "text": text,
            "contextStartSeconds": round(rows[0][0], 2),
            "contextEndSeconds": round(max(row[1] for row in rows), 2),
            "context": context,
        })
    candidates.sort(key=lambda item: item["score"], reverse=True)
    selected = []
    for candidate in candidates:
        if any(abs(candidate["startSeconds"] - existing["startSeconds"]) < 4 for existing in selected):
            continue
        selected.append(candidate)
        if len(selected) >= 30:
            break
    return selected


def main() -> int:
    plan = read_json(ROOT / "validation" / "all-unique-candidate-plan.json")
    pre_exact = load_pre_exact()
    case_numbers = plan["withoutCandidates"]
    results: dict[str, Any] = {}

    def process(case_number: str) -> tuple[str, Any]:
        claim = pre_exact[case_number]
        video_id = claim["media"]["youtubeId"]
        segments = fetch(video_id)
        transcript_end = max((parsed(segment) or (0, 0, ""))[1] for segment in segments)
        return case_number, {
            "person": claim["person"],
            "verdict": claim["verdict"],
            "originalClaim": claim["claim"],
            "youtubeId": video_id,
            "configuredDurationSeconds": claim["media"]["videoDurationSeconds"],
            "transcriptEndSeconds": round(transcript_end, 2),
            "lines": rank(claim, segments),
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(process, case_number): case_number for case_number in case_numbers}
        for future in concurrent.futures.as_completed(futures):
            case_number = futures[future]
            try:
                fetched_case, result = future.result()
                results[fetched_case] = result
                print(f"{fetched_case}: {len(result['lines'])} candidate lines", flush=True)
            except Exception as exc:  # noqa: BLE001
                results[case_number] = {"error": f"{type(exc).__name__}: {exc}"}
                print(f"{case_number}: FAILED", flush=True)

    OUTPUT.write_text(json.dumps({"cases": results}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    failures = [case for case, value in results.items() if value.get("error")]
    print(f"Completed {len(results) - len(failures)}/{len(results)} missing-source inventories.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
