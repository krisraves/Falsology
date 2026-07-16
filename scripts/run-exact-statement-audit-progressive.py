#!/usr/bin/env python3
"""Progressively generate exact statement windows without losing successful work.

Each invocation fetches only unresolved source videos, writes successful case
matches to a local progress file immediately, and returns success only after all
50 cases have exact transcript-backed windows. The workflow can safely invoke
this script repeatedly to retry only unavailable or rate-limited sources.
"""

from __future__ import annotations

import concurrent.futures
import importlib.util
import json
import os
import random
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "scripts" / "audit-exact-statement-clips.py"
PROGRESS_PATH = ROOT / "validation" / "exact-statement-progress.json"
ENDPOINT = "https://youtube2text.diguardia.org/api/transcript"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
MAX_WORKERS = int(os.environ.get("AUDIT_WORKERS", "12"))
REQUEST_TIMEOUT_SECONDS = int(os.environ.get("AUDIT_REQUEST_TIMEOUT", "80"))


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


def read_progress() -> dict[str, Any]:
    if not PROGRESS_PATH.exists():
        return {"provider": ENDPOINT, "windows": {}, "attempts": {}, "failures": {}, "matches": {}}
    value = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("Progress file is not an object")
    value.setdefault("provider", ENDPOINT)
    value.setdefault("windows", {})
    value.setdefault("attempts", {})
    value.setdefault("failures", {})
    value.setdefault("matches", {})
    return value


def post_transcript(video_id: str) -> dict[str, Any]:
    body = json.dumps(
        {"url": f"https://www.youtube.com/watch?v={video_id}", "lang": "en"}
    ).encode("utf-8")
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
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        payload = response.read()
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}")
    value = json.loads(payload.decode("utf-8", errors="replace"))
    if not isinstance(value, dict) or not isinstance(value.get("segments"), list) or not value["segments"]:
        raise RuntimeError("Transcript endpoint returned no timed segments")
    return value


def captions_from_response(audit: Any, value: dict[str, Any]) -> list[Any]:
    captions: list[Any] = []
    for segment in value["segments"]:
        if not isinstance(segment, dict):
            continue
        text = str(segment.get("text", "")).strip()
        try:
            start = float(segment.get("start", 0.0))
            duration = float(segment.get("duration", 0.0))
        except (TypeError, ValueError):
            continue
        if text and start >= 0 and duration > 0:
            captions.append(audit.Caption(text, start, duration))
    if not captions:
        raise RuntimeError("Transcript response contained no usable captions")
    return captions


def error_text(exc: BaseException) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")[:600]
        except Exception:  # noqa: BLE001
            pass
        return f"HTTP {exc.code}: {body}".strip()
    return f"{type(exc).__name__}: {exc}"


def build_window(audit: Any, claim: dict[str, Any], captions: list[Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    words = audit.to_timed_words(captions)
    statement_start, statement_end, score, match_text = audit.locate_statement(
        words, audit.query_variants(claim)
    )
    if score < audit.MIN_ACCEPTED_SCORE:
        raise RuntimeError(
            f"Best transcript match scored {score:.1f}, below {audit.MIN_ACCEPTED_SCORE:.1f}"
        )

    statement_start = audit.round_tenth(statement_start)
    statement_end = audit.round_tenth(statement_end)
    duration = float(claim["media"]["videoDurationSeconds"])
    start, end = audit.exact_window(statement_start, statement_end, duration)
    if end <= start:
        raise RuntimeError(f"Invalid generated range {start}-{end}")

    video_id = str(claim["media"]["youtubeId"])
    window = {
        "media": {
            "startSeconds": start,
            "endSeconds": end,
            "statementStartSeconds": statement_start,
            "statementEndSeconds": statement_end,
            "transcriptMatchScore": audit.round_tenth(score),
            "transcriptMatchText": match_text,
            "url": f"https://www.youtube.com/watch?v={video_id}&t={start:g}s",
            "verifiedAt": "2026-07-16",
        }
    }
    match = {
        "caseNumber": claim["caseNumber"],
        "person": claim["person"],
        "videoId": video_id,
        "query": audit.query_variants(claim),
        "matchedText": match_text,
        "score": audit.round_tenth(score),
        "statementStartSeconds": statement_start,
        "statementEndSeconds": statement_end,
        "startSeconds": start,
        "endSeconds": end,
    }
    return window, match


def main() -> int:
    audit = load_module()
    claims = audit.load_final_claims()
    if len(claims) != 50:
        raise RuntimeError(f"Expected 50 claims, found {len(claims)}")

    claims_by_video: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for claim in claims:
        claims_by_video[str(claim["media"]["youtubeId"])].append(claim)

    progress = read_progress()
    windows: dict[str, Any] = progress["windows"]
    attempts: dict[str, int] = progress["attempts"]
    failures: dict[str, str] = progress["failures"]
    matches: dict[str, Any] = progress["matches"]

    resolved_videos = {
        video_id
        for video_id, grouped_claims in claims_by_video.items()
        if all(claim["caseNumber"] in windows for claim in grouped_claims)
    }
    unresolved = [video_id for video_id in claims_by_video if video_id not in resolved_videos]

    print(
        f"Progress: {len(windows)}/50 cases resolved; fetching {len(unresolved)} unresolved source(s) "
        f"with {MAX_WORKERS} workers and {REQUEST_TIMEOUT_SECONDS}s timeout.",
        flush=True,
    )

    if unresolved:
        lock = threading.Lock()
        completed = 0

        def fetch(video_id: str) -> tuple[str, dict[str, Any]]:
            jitter = random.uniform(0.0, 1.5)
            time.sleep(jitter)
            return video_id, post_transcript(video_id)

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(unresolved))) as executor:
            future_map = {executor.submit(fetch, video_id): video_id for video_id in unresolved}
            for future in concurrent.futures.as_completed(future_map):
                video_id = future_map[future]
                attempts[video_id] = int(attempts.get(video_id, 0)) + 1
                try:
                    fetched_id, value = future.result()
                    captions = captions_from_response(audit, value)
                    generated: dict[str, Any] = {}
                    generated_matches: dict[str, Any] = {}
                    for claim in claims_by_video[fetched_id]:
                        window, match = build_window(audit, claim, captions)
                        generated[claim["caseNumber"]] = window
                        generated_matches[claim["caseNumber"]] = match
                    with lock:
                        windows.update(generated)
                        matches.update(generated_matches)
                        failures.pop(fetched_id, None)
                    state = f"ok ({len(generated)} case(s))"
                except Exception as exc:  # noqa: BLE001
                    with lock:
                        failures[video_id] = error_text(exc)
                    state = "FAILED"

                completed += 1
                progress.update(
                    {
                        "provider": ENDPOINT,
                        "windows": windows,
                        "attempts": attempts,
                        "failures": failures,
                        "matches": matches,
                        "resolvedCases": len(windows),
                        "totalCases": 50,
                    }
                )
                atomic_json(PROGRESS_PATH, progress)
                print(f"[{completed:02d}/{len(unresolved)}] {video_id}: {state}", flush=True)

    missing_cases = [claim["caseNumber"] for claim in claims if claim["caseNumber"] not in windows]
    progress.update(
        {
            "provider": ENDPOINT,
            "windows": windows,
            "attempts": attempts,
            "failures": failures,
            "matches": matches,
            "resolvedCases": len(windows),
            "totalCases": 50,
            "missingCases": missing_cases,
        }
    )
    atomic_json(PROGRESS_PATH, progress)

    if missing_cases:
        print(
            f"Incomplete audit: {len(windows)}/50 cases resolved; {len(missing_cases)} remain.",
            file=sys.stderr,
        )
        return 2

    ordered_windows = {claim["caseNumber"]: windows[claim["caseNumber"]] for claim in claims}
    audit.write_json(audit.WINDOWS_PATH, ordered_windows)
    audit.patch_application()
    print("All 50 exact statement windows generated and application patches applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
