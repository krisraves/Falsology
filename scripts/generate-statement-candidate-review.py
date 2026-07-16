#!/usr/bin/env python3
"""Generate human-reviewable exact quote candidates for every Falsology case.

The previous matcher operated on overlapping caption rows as if they were a
monotonic word stream. That produced duplicated words, false positives, and
occasionally reversed timings. This review generator scores non-overlapping
caption windows, reconstructs their spoken text, and writes the five strongest
candidates per case with surrounding context. It never modifies production
case data.
"""

from __future__ import annotations

import concurrent.futures
import importlib.util
import json
import math
import os
import random
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "scripts" / "audit-exact-statement-clips.py"
OUTPUT_PATH = ROOT / "validation" / "statement-candidate-review.json"
ENDPOINT = "https://youtube2text.diguardia.org/api/transcript"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
MAX_WORKERS = int(os.environ.get("CANDIDATE_WORKERS", "12"))
REQUEST_TIMEOUT = int(os.environ.get("CANDIDATE_TIMEOUT", "90"))
MAX_CANDIDATES = 8

STOPWORDS = {
    "a", "about", "after", "again", "all", "am", "an", "and", "any", "are", "as", "at", "be", "because",
    "been", "before", "being", "but", "by", "can", "could", "did", "do", "does", "doing", "for", "from",
    "had", "has", "have", "he", "her", "here", "hers", "him", "his", "how", "i", "if", "in", "into",
    "is", "it", "its", "just", "me", "my", "no", "not", "of", "on", "or", "our", "out", "right",
    "she", "so", "some", "that", "the", "their", "them", "then", "there", "they", "this", "to", "up",
    "was", "we", "were", "what", "when", "where", "which", "who", "why", "with", "would", "you", "your",
}


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str
    tokens: tuple[str, ...]


def load_module() -> Any:
    spec = importlib.util.spec_from_file_location("falsology_exact_statement_audit", AUDIT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {AUDIT_PATH}")
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


def normalize_token(value: str) -> str:
    value = value.lower().replace("’", "'")
    value = re.sub(r"[^a-z0-9']+", "", value)
    value = value.replace("'", "")
    replacements = {
        "wifes": "wife",
        "childrens": "children",
        "theyre": "theyre",
        "im": "im",
        "ive": "ive",
        "wasnt": "wasnt",
        "didnt": "didnt",
        "dont": "dont",
        "cant": "cant",
    }
    return replacements.get(value, value)


def tokenize(text: str) -> tuple[str, ...]:
    return tuple(token for raw in text.split() if (token := normalize_token(raw)))


def stem(token: str) -> str:
    if len(token) > 5 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 5 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 4 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 4 and token.endswith("es"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def content_tokens(tokens: tuple[str, ...] | list[str]) -> list[str]:
    return [stem(token) for token in tokens if token not in STOPWORDS and len(token) >= 3]


def merge_tokens(left: list[str], right: tuple[str, ...]) -> list[str]:
    if not left:
        return list(right)
    maximum = min(len(left), len(right), 18)
    overlap = 0
    for size in range(maximum, 0, -1):
        if left[-size:] == list(right[:size]):
            overlap = size
            break
    return left + list(right[overlap:])


def phrase_for_window(segments: list[Segment], first: int, last: int) -> str:
    merged: list[str] = []
    for segment in segments[first : last + 1]:
        merged = merge_tokens(merged, segment.tokens)
    return " ".join(merged)


def fetch_transcript(video_id: str) -> list[Segment]:
    body = json.dumps({"url": f"https://www.youtube.com/watch?v={video_id}", "lang": "en"}).encode("utf-8")
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
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        payload = response.read()
    value = json.loads(payload.decode("utf-8", errors="replace"))
    rows = value.get("segments") if isinstance(value, dict) else None
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("Transcript endpoint returned no timed segments")

    segments: list[Segment] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        text = str(row.get("text", "")).strip()
        try:
            start = float(row.get("start", 0.0))
            duration = float(row.get("duration", 0.0))
        except (TypeError, ValueError):
            continue
        row_tokens = tokenize(text)
        if text and row_tokens and start >= 0 and duration > 0:
            segments.append(Segment(start=start, end=start + duration, text=text, tokens=row_tokens))
    if not segments:
        raise RuntimeError("Transcript contained no usable timed segments")
    return segments


def query_bundle(claim: dict[str, Any]) -> dict[str, Any]:
    claim_text = str(claim.get("claim", ""))
    transcript_text = str(claim.get("transcript", ""))
    context = str(claim.get("context", ""))
    classification = str(claim.get("classification", ""))
    short = str(claim.get("shortExplanation", ""))
    variants = []
    for value in (transcript_text, claim_text):
        normalized = " ".join(tokenize(value))
        if normalized and normalized not in variants:
            variants.append(normalized)
    primary = variants[0] if variants else ""
    primary_tokens = tokenize(primary)
    primary_content = content_tokens(primary_tokens)
    support_tokens = content_tokens(tokenize(" ".join((context, classification, short))))
    return {
        "variants": variants,
        "primary": primary,
        "tokens": primary_tokens,
        "content": primary_content,
        "support": support_tokens,
    }


def score_window(bundle: dict[str, Any], text: str) -> dict[str, float]:
    candidate_tokens = tokenize(text)
    candidate_content = content_tokens(candidate_tokens)
    query_content = bundle["content"]
    support_content = bundle["support"]

    query_counter = Counter(query_content)
    candidate_counter = Counter(candidate_content)
    overlap = sum((query_counter & candidate_counter).values())
    coverage = overlap / max(1, sum(query_counter.values()))
    precision = overlap / max(1, sum(candidate_counter.values()))

    support_counter = Counter(support_content)
    support_overlap = sum((support_counter & candidate_counter).values())
    support_coverage = support_overlap / max(1, min(8, sum(support_counter.values())))

    phrase = " ".join(candidate_tokens)
    variant_scores = [
        max(
            fuzz.ratio(variant, phrase),
            fuzz.partial_ratio(variant, phrase) * 0.92,
            fuzz.token_sort_ratio(variant, phrase) * 0.94,
        )
        for variant in bundle["variants"]
    ] or [0.0]
    fuzzy = max(variant_scores) / 100.0

    distinct_overlap = len(set(query_content) & set(candidate_content))
    phrase_length = len(candidate_tokens)
    length_score = 1.0 if 4 <= phrase_length <= 28 else max(0.0, 1.0 - abs(phrase_length - 16) / 45)
    generic_penalty = 0.0
    if distinct_overlap == 0:
        generic_penalty += 0.55
    elif distinct_overlap == 1 and len(set(query_content)) >= 3:
        generic_penalty += 0.28
    if phrase_length < 3:
        generic_penalty += 0.4

    total = (
        coverage * 48
        + precision * 12
        + fuzzy * 24
        + min(1.0, support_coverage) * 8
        + min(1.0, distinct_overlap / 4) * 6
        + length_score * 2
        - generic_penalty * 100
    )
    return {
        "score": round(total, 2),
        "coverage": round(coverage, 3),
        "precision": round(precision, 3),
        "fuzzy": round(fuzzy, 3),
        "supportCoverage": round(support_coverage, 3),
        "distinctContentOverlap": float(distinct_overlap),
    }


def candidate_windows(claim: dict[str, Any], segments: list[Segment]) -> list[dict[str, Any]]:
    bundle = query_bundle(claim)
    scored: list[dict[str, Any]] = []
    maximum_segments = 8

    for first in range(len(segments)):
        for last in range(first, min(len(segments), first + maximum_segments)):
            start = segments[first].start
            end = max(segment.end for segment in segments[first : last + 1])
            if end - start > 32:
                break
            text = phrase_for_window(segments, first, last)
            token_count = len(tokenize(text))
            if token_count < 3 or token_count > 45:
                continue
            metrics = score_window(bundle, text)
            if metrics["score"] < 20:
                continue
            context_first = max(0, first - 2)
            context_last = min(len(segments) - 1, last + 2)
            context_text = phrase_for_window(segments, context_first, context_last)
            scored.append(
                {
                    **metrics,
                    "startSeconds": round(start, 2),
                    "endSeconds": round(end, 2),
                    "durationSeconds": round(end - start, 2),
                    "text": text,
                    "context": context_text,
                    "firstSegment": first,
                    "lastSegment": last,
                }
            )

    scored.sort(key=lambda item: item["score"], reverse=True)
    selected: list[dict[str, Any]] = []
    for candidate in scored:
        duplicate = False
        for existing in selected:
            intersection = max(0.0, min(candidate["endSeconds"], existing["endSeconds"]) - max(candidate["startSeconds"], existing["startSeconds"]))
            union = max(candidate["endSeconds"], existing["endSeconds"]) - min(candidate["startSeconds"], existing["startSeconds"])
            if union > 0 and intersection / union > 0.55:
                duplicate = True
                break
            if fuzz.ratio(candidate["text"], existing["text"]) > 86:
                duplicate = True
                break
        if not duplicate:
            selected.append(candidate)
        if len(selected) >= MAX_CANDIDATES:
            break
    return selected


def load_existing() -> dict[str, Any]:
    if not OUTPUT_PATH.exists():
        return {"provider": ENDPOINT, "cases": {}, "failures": {}, "resolved": 0, "total": 50}
    try:
        value = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
        if isinstance(value, dict):
            value.setdefault("provider", ENDPOINT)
            value.setdefault("cases", {})
            value.setdefault("failures", {})
            return value
    except Exception:  # noqa: BLE001
        pass
    return {"provider": ENDPOINT, "cases": {}, "failures": {}, "resolved": 0, "total": 50}


def main() -> int:
    audit = load_module()
    claims = audit.load_final_claims()
    by_video: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for claim in claims:
        by_video[str(claim["media"]["youtubeId"])].append(claim)

    report = load_existing()
    completed_cases = set(report["cases"])
    unresolved_videos = [
        video_id
        for video_id, grouped in by_video.items()
        if not all(claim["caseNumber"] in completed_cases for claim in grouped)
    ]

    print(f"Generating candidate review for {len(unresolved_videos)} source video(s).", flush=True)
    if not unresolved_videos:
        return 0

    def fetch(video_id: str) -> tuple[str, list[Segment]]:
        time.sleep(random.uniform(0.0, 1.2))
        return video_id, fetch_transcript(video_id)

    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(unresolved_videos))) as executor:
        future_map = {executor.submit(fetch, video_id): video_id for video_id in unresolved_videos}
        for future in concurrent.futures.as_completed(future_map):
            video_id = future_map[future]
            try:
                fetched_id, segments = future.result()
                for claim in by_video[fetched_id]:
                    candidates = candidate_windows(claim, segments)
                    report["cases"][claim["caseNumber"]] = {
                        "person": claim["person"],
                        "verdict": claim["verdict"],
                        "claim": claim["claim"],
                        "transcript": claim.get("transcript"),
                        "videoId": fetched_id,
                        "videoDurationSeconds": claim["media"]["videoDurationSeconds"],
                        "candidates": candidates,
                    }
                    if not candidates:
                        report["failures"][claim["caseNumber"]] = "No candidate window scored above the minimum."
                    else:
                        report["failures"].pop(claim["caseNumber"], None)
            except Exception as exc:  # noqa: BLE001
                for claim in by_video[video_id]:
                    report["failures"][claim["caseNumber"]] = f"{type(exc).__name__}: {exc}"
            completed += 1
            report["resolved"] = len(report["cases"])
            report["total"] = len(claims)
            atomic_json(OUTPUT_PATH, report)
            print(f"[{completed:02d}/{len(unresolved_videos)}] {video_id}", flush=True)

    return 0 if len(report["cases"]) == len(claims) else 2


if __name__ == "__main__":
    raise SystemExit(main())
