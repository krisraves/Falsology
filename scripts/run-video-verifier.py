#!/usr/bin/env python3
"""Run the candidate verifier with stricter matching and public metadata fallbacks."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from typing import Any

import requests

SCRIPT = Path(__file__).with_name("verify-video-candidates.py")
spec = importlib.util.spec_from_file_location("falsology_video_verifier", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load candidate verifier")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Negation is materially important to truth/lie statements and must remain in
# the lexical comparison. Avoid loose pronoun patterns such as `were` or `ill`.
module.MATCH_STOP_WORDS.discard("not")
module.MATCH_STOP_WORDS.discard("never")
module.FIRST_PERSON = re.compile(
    r"\b(i|i'm|im|i've|ive|i'd|i'll|me|my|mine|we|we're|weve|we've|our|ours)\b",
    re.I,
)

estimated_duration_ids: set[str] = set()
original_verify_candidate = module.verify_candidate


def public_metadata(video_id: str) -> dict[str, Any]:
    """Use public YouTube web endpoints when yt-dlp is challenged as a bot."""
    session = requests.Session()
    headers = {"User-Agent": module.USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
    watch_url = f"https://www.youtube.com/watch?v={video_id}"
    embed_url = f"https://www.youtube-nocookie.com/embed/{video_id}"
    oembed_url = "https://www.youtube.com/oembed"

    try:
        oembed = session.get(
            oembed_url,
            params={"url": watch_url, "format": "json"},
            headers=headers,
            timeout=25,
        )
        if oembed.status_code != 200:
            return {"ok": False, "error": f"YouTube oEmbed returned HTTP {oembed.status_code}"}
        payload = oembed.json()

        watch = session.get(watch_url, headers=headers, timeout=30)
        embed = session.get(embed_url, headers=headers, timeout=30)
        combined = f"{watch.text}\n{embed.text}"

        duration: float | None = None
        for pattern, divisor in (
            (r'"lengthSeconds":"(\d+)"', 1),
            (r'"approxDurationMs":"(\d+)"', 1000),
            (r'"durationMs":"(\d+)"', 1000),
        ):
            match = re.search(pattern, combined)
            if match:
                duration = float(match.group(1)) / divisor
                break
        if duration is None:
            # Continue the remaining gates, but never allow automatic promotion
            # when source duration could not be independently read.
            duration = 86400.0
            estimated_duration_ids.add(video_id)

        status_match = re.search(r'"playabilityStatus":\{"status":"([A-Z_]+)"', combined)
        playability_status = status_match.group(1) if status_match else "UNKNOWN"
        unavailable_phrases = (
            "Video unavailable",
            "This video is unavailable",
            "Private video",
            "This video has been removed",
        )
        unavailable = any(phrase.lower() in combined.lower() for phrase in unavailable_phrases)
        embed_blocked = playability_status in {"UNPLAYABLE", "LOGIN_REQUIRED", "ERROR", "AGE_CHECK_REQUIRED"}
        playable = embed.status_code == 200 and not unavailable and not embed_blocked
        is_live = bool(re.search(r'"isLive(Content)?":true', combined))

        info = {
            "id": video_id,
            "title": payload.get("title") or "",
            "channel": payload.get("author_name") or "",
            "uploader": payload.get("author_name") or "",
            "duration": duration,
            "availability": "public",
            "live_status": "is_live" if is_live else "not_live",
            "is_live": is_live,
            "playable_in_embed": playable,
            "age_limit": 0,
            "webpage_url": watch_url,
            "description": "",
            "subtitles": {},
            "automatic_captions": {},
        }
        return {"ok": True, "info": info}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"public metadata fallback failed: {type(exc).__name__}: {exc}"}


module.run_metadata = public_metadata


def verified_with_duration_guard(candidate: dict[str, Any], duplicate_ids: set[str]) -> dict[str, Any]:
    result = original_verify_candidate(candidate, duplicate_ids)
    if candidate["videoId"] in estimated_duration_ids:
        result.setdefault("checks", {})["sourceDurationConfirmed"] = False
        result.setdefault("issues", []).append("Source duration could not be confirmed from YouTube's public page")
        if result.get("verificationStatus") == "verified":
            result["verificationStatus"] = "needs_editorial_review"
    else:
        result.setdefault("checks", {})["sourceDurationConfirmed"] = True
    return result


module.verify_candidate = verified_with_duration_guard

# Force a new method version so completed reports from the blocked yt-dlp pass
# are not reused by the workflow.
original_main = module.main


def main() -> int:
    code = original_main()
    report_path = module.REPORT
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["methodVersion"] = 2
    report["metadataMethod"] = "youtube-oembed-watch-embed-plus-timed-transcript"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return code


raise SystemExit(main())
