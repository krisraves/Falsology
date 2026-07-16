#!/usr/bin/env python3
"""Generate exact statement-centered windows from hosted timestamped transcripts."""

from __future__ import annotations

import concurrent.futures
import importlib.util
import json
import random
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "scripts" / "audit-exact-statement-clips.py"
ENDPOINT = "https://youtube2text.diguardia.org/api/transcript"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
MAX_WORKERS = 4
REQUEST_TIMEOUT_SECONDS = 150
MAX_ATTEMPTS = 4


def load_audit_module() -> Any:
    spec = importlib.util.spec_from_file_location("falsology_exact_statement_audit", AUDIT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {AUDIT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def post_transcript(video_id: str) -> dict[str, Any]:
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    body = json.dumps({"url": video_url, "lang": "en"}).encode("utf-8")
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
        if not isinstance(value, dict):
            raise RuntimeError("Transcript response was not an object")
        segments = value.get("segments")
        if not isinstance(segments, list) or not segments:
            raise RuntimeError("Transcript response contained no timed segments")
        return value


def fetch_with_retries(video_id: str) -> dict[str, Any]:
    errors: list[str] = []
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return post_transcript(video_id)
        except urllib.error.HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8", errors="replace")[:1000]
            except Exception:  # noqa: BLE001
                pass
            errors.append(f"attempt {attempt}: HTTP {exc.code} {body}")
            if exc.code not in (408, 425, 429, 500, 502, 503, 504):
                break
        except Exception as exc:  # noqa: BLE001
            errors.append(f"attempt {attempt}: {type(exc).__name__}: {exc}")
        if attempt < MAX_ATTEMPTS:
            time.sleep(min(20.0, 2.5 * (2 ** (attempt - 1))) + random.random())
    raise RuntimeError(" | ".join(errors))


def main() -> int:
    audit = load_audit_module()
    claims = audit.load_final_claims()
    video_ids = list(dict.fromkeys(str(claim["media"]["youtubeId"]) for claim in claims))
    print(f"Fetching {len(video_ids)} unique timestamped transcripts with {MAX_WORKERS} workers.", flush=True)

    cache: dict[str, list[Any]] = {}
    failures: dict[str, str] = {}
    lock = threading.Lock()
    completed = 0

    def fetch_one(video_id: str) -> tuple[str, list[Any]]:
        value = fetch_with_retries(video_id)
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
            raise RuntimeError("No usable timed caption segments")
        return video_id, captions

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {executor.submit(fetch_one, video_id): video_id for video_id in video_ids}
        for future in concurrent.futures.as_completed(future_map):
            video_id = future_map[future]
            try:
                fetched_id, captions = future.result()
                with lock:
                    cache[fetched_id] = captions
            except Exception as exc:  # noqa: BLE001
                with lock:
                    failures[video_id] = f"{type(exc).__name__}: {exc}"
            completed += 1
            state = "ok" if video_id in cache else "FAILED"
            print(f"[{completed:02d}/{len(video_ids)}] {video_id}: {state}", flush=True)

    if failures:
        report = {
            "provider": ENDPOINT,
            "requested": len(video_ids),
            "succeeded": len(cache),
            "failures": failures,
        }
        audit.REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        audit.REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Transcript fetch failed for {len(failures)} source(s).", file=sys.stderr)
        return 1

    def fetch_from_cache(video_id: str) -> list[Any]:
        captions = cache.get(video_id)
        if not captions:
            raise RuntimeError(f"No cached transcript for {video_id}")
        return captions

    audit.fetch_captions = fetch_from_cache
    return int(audit.main())


if __name__ == "__main__":
    raise SystemExit(main())
