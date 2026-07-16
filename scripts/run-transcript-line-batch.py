#!/usr/bin/env python3
"""Fetch and rank first-person transcript lines for a controlled case batch.

Set CASES to a comma-separated list of case numbers. Results merge into
validation/problem-source-lines.json so each workflow run can process a small,
rate-limit-safe batch without discarding prior successful transcripts.
"""

from __future__ import annotations

import concurrent.futures
import importlib.util
import json
import os
import random
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "scripts" / "audit-exact-statement-clips.py"
OUTPUT = ROOT / "validation" / "problem-source-lines.json"
ENDPOINT = "https://youtube2text.diguardia.org/api/transcript"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
TIMEOUT = int(os.environ.get("TRANSCRIPT_TIMEOUT", "90"))
WORKERS = int(os.environ.get("TRANSCRIPT_WORKERS", "3"))
ATTEMPTS = int(os.environ.get("TRANSCRIPT_ATTEMPTS", "4"))
REQUESTED = [value.strip().upper() for value in os.environ.get("CASES", "").split(",") if value.strip()]

FIRST_PERSON = re.compile(r"\b(i|i'm|im|i've|ive|i'd|id|i'll|ill|me|my|mine|we|we're|were|we've|our|ours)\b", re.I)
QUESTION = re.compile(r"\b(did you|do you|are you|were you|can you|could you|would you|tell me|what did|why did|how did)\b", re.I)
STOP = {
    "about", "after", "again", "also", "and", "are", "because", "been", "before", "being", "but", "could",
    "does", "doing", "from", "have", "into", "just", "more", "most", "that", "their", "them", "then", "there",
    "these", "they", "this", "those", "through", "very", "what", "when", "where", "which", "with", "would", "your",
}


def load_audit() -> Any:
    spec = importlib.util.spec_from_file_location("falsology_batch_audit", AUDIT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load case audit module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def normalize(text: str) -> list[str]:
    return [word for word in re.sub(r"[^a-z0-9]+", " ", text.lower()).split() if len(word) >= 3 and word not in STOP]


def request_transcript(video_id: str) -> dict[str, Any]:
    body = json.dumps({"url": f"https://www.youtube.com/watch?v={video_id}", "lang": "en"}).encode()
    errors: list[str] = []
    for attempt in range(1, ATTEMPTS + 1):
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
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                value = json.loads(response.read().decode("utf-8", errors="replace"))
            if not isinstance(value, dict) or not isinstance(value.get("segments"), list) or not value["segments"]:
                raise RuntimeError("No timestamped transcript segments returned")
            return value
        except Exception as exc:  # noqa: BLE001
            detail = ""
            if isinstance(exc, urllib.error.HTTPError):
                try:
                    detail = exc.read().decode("utf-8", errors="replace")[:500]
                except Exception:  # noqa: BLE001
                    pass
            errors.append(f"attempt {attempt}: {type(exc).__name__}: {exc} {detail}".strip())
            if attempt < ATTEMPTS:
                time.sleep(attempt * 7 + random.uniform(0.5, 2.5))
    raise RuntimeError(" | ".join(errors))


def segment_value(segment: dict[str, Any]) -> tuple[float, float, str] | None:
    text = " ".join(str(segment.get("text", "")).split())
    try:
        start = float(segment.get("start", 0))
        duration = float(segment.get("duration", 0))
    except (TypeError, ValueError):
        return None
    if not text or start < 0 or duration <= 0:
        return None
    return start, start + duration, text


def rank_lines(claim: dict[str, Any], segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    relevance = Counter(normalize(" ".join([
        str(claim.get("claim", "")), str(claim.get("context", "")), str(claim.get("fullTruth", "")),
        str(claim.get("classification", "")), str(claim.get("shortExplanation", "")),
    ])))
    candidates: list[dict[str, Any]] = []
    for index, segment in enumerate(segments):
        value = segment_value(segment)
        if not value:
            continue
        start, end, text = value
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
        first = max(0, index - 3)
        last = min(len(segments), index + 4)
        context_rows = [segment_value(row) for row in segments[first:last]]
        context_rows = [row for row in context_rows if row]
        if not context_rows:
            continue
        context_start = context_rows[0][0]
        context_end = max(row[1] for row in context_rows)
        context = " ".join(row[2] for row in context_rows)
        candidates.append({
            "score": round(score, 2),
            "startSeconds": round(start, 2),
            "endSeconds": round(end, 2),
            "text": text,
            "contextStartSeconds": round(context_start, 2),
            "contextEndSeconds": round(context_end, 2),
            "context": context,
        })
    candidates.sort(key=lambda item: item["score"], reverse=True)
    selected: list[dict[str, Any]] = []
    for candidate in candidates:
        if any(abs(candidate["startSeconds"] - existing["startSeconds"]) < 3.5 for existing in selected):
            continue
        selected.append(candidate)
        if len(selected) >= 30:
            break
    return selected


def load_output() -> dict[str, Any]:
    if OUTPUT.exists():
        try:
            value = json.loads(OUTPUT.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                return value
        except Exception:  # noqa: BLE001
            pass
    return {"provider": ENDPOINT, "cases": {}}


def main() -> int:
    if not REQUESTED:
        raise RuntimeError("CASES environment variable is required")
    audit = load_audit()
    all_claims = {claim["caseNumber"]: claim for claim in audit.load_final_claims()}
    missing = [case for case in REQUESTED if case not in all_claims]
    if missing:
        raise RuntimeError(f"Unknown case numbers: {', '.join(missing)}")
    output = load_output()
    output.setdefault("provider", ENDPOINT)
    output.setdefault("cases", {})

    def process(case_number: str) -> tuple[str, dict[str, Any]]:
        claim = all_claims[case_number]
        video_id = str(claim["media"]["youtubeId"])
        value = request_transcript(video_id)
        segments = [row for row in value["segments"] if isinstance(row, dict)]
        transcript_end = 0.0
        for segment in segments:
            parsed = segment_value(segment)
            if parsed:
                transcript_end = max(transcript_end, parsed[1])
        return case_number, {
            "person": claim["person"],
            "verdict": claim["verdict"],
            "originalClaim": claim["claim"],
            "videoId": video_id,
            "configuredDurationSeconds": claim["media"]["videoDurationSeconds"],
            "transcriptEndSeconds": round(transcript_end, 2),
            "lines": rank_lines(claim, segments),
        }

    failures = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(WORKERS, len(REQUESTED))) as executor:
        future_map = {executor.submit(process, case): case for case in REQUESTED}
        for future in concurrent.futures.as_completed(future_map):
            case_number = future_map[future]
            try:
                fetched_case, result = future.result()
                output["cases"][fetched_case] = result
                print(f"{fetched_case}: {len(result['lines'])} direct-line candidate(s)", flush=True)
            except Exception as exc:  # noqa: BLE001
                failures += 1
                output["cases"][case_number] = {
                    "error": f"{type(exc).__name__}: {exc}",
                    "attemptedAt": "2026-07-16",
                }
                print(f"{case_number}: FAILED", flush=True)
            atomic_json(OUTPUT, output)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
