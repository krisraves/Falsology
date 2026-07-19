#!/usr/bin/env python3
"""Second-stage content build: reuse verified sources and fill remaining quotas."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

import requests

SCRIPT = Path(__file__).with_name("build-verified-content-deck.py")
spec = importlib.util.spec_from_file_location("falsology_content_builder_v6", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load content builder")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

PRIOR_REPORT = module.REPORT_PATH
prior = json.loads(PRIOR_REPORT.read_text(encoding="utf-8")) if PRIOR_REPORT.exists() else {}
cached_by_seed = {
    str(result.get("seed", {}).get("seedId")): list(result.get("candidates") or [])
    for result in prior.get("seedResults", [])
}

TRUTH_ANCHORS = {
    "innocent", "prison", "years", "year", "death", "row", "dna", "exonerated", "convicted",
    "wrongfully", "survived", "trapped", "captive", "kidnapped", "days", "hours", "months",
    "mine", "ocean", "sea", "mountain", "plane", "lightning", "radiation", "warned", "escaped",
}


def parse_segments(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        payload = payload.get("segments") or payload.get("transcript") or payload.get("data") or payload.get("result") or []
        if isinstance(payload, dict):
            payload = payload.get("segments") or payload.get("transcript") or payload.get("data") or []
    if not isinstance(payload, list):
        return []
    output: list[dict[str, Any]] = []
    for raw in payload:
        if not isinstance(raw, dict):
            continue
        text = str(raw.get("text") or raw.get("content") or raw.get("utf8") or "").strip()
        try:
            start = float(raw.get("start"))
            if raw.get("duration") is not None:
                duration = max(0.05, float(raw.get("duration")))
            else:
                duration = max(0.05, float(raw.get("end")) - start)
        except (TypeError, ValueError):
            continue
        if text:
            output.append({"text": text, "start": start, "duration": duration})
    output.sort(key=lambda item: item["start"])
    return output


def timed_transcript(video_id: str) -> list[dict[str, Any]]:
    try:
        response = requests.post(
            module.TRANSCRIPT_ENDPOINT,
            json={"url": f"https://www.youtube.com/watch?v={video_id}"},
            headers=module.HEADERS,
            timeout=22,
        )
        if response.status_code == 200:
            return parse_segments(response.json())
    except Exception:
        pass
    return []


def public_metadata(video_id: str) -> dict[str, Any] | None:
    try:
        response = requests.get(
            f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json",
            headers=module.HEADERS,
            timeout=15,
        )
        if response.status_code != 200:
            return None
        data = response.json()
        return {
            "title": str(data.get("title") or ""),
            "channel": str(data.get("author_name") or "YouTube source channel"),
            "embeddable": True,
        }
    except Exception:
        return None


def precise_extract_statement(segments: list[dict[str, Any]], seed: dict[str, Any]) -> dict[str, Any] | None:
    hints = [str(value) for value in seed.get("statementHints", [])]
    hint_tokens = set().union(*(module.meaningful_tokens(value) for value in hints)) if hints else set()
    fact_tokens = module.meaningful_tokens(str(seed.get("factSummary") or ""))
    evidence_tokens = module.meaningful_tokens(str(seed.get("evidenceQuery") or ""))
    context_tokens = hint_tokens | fact_tokens | evidence_tokens
    best: dict[str, Any] | None = None

    for left in range(len(segments)):
        parts: list[str] = []
        for right in range(left, min(len(segments), left + 7)):
            parts.append(segments[right]["text"])
            raw_text = re.sub(r"\s+", " ", " ".join(parts)).strip()
            first_person = module.FIRST_PERSON.search(raw_text)
            if not first_person:
                continue
            # The first-person line must begin near the start of the caption
            # window, preventing a reporter narration from becoming the claim.
            leading_words = len(module.normalize(raw_text[: first_person.start()]).split())
            if leading_words > 5:
                continue
            statement_text = raw_text[first_person.start() :].strip(" -:,.\"")
            normalized = module.normalize(statement_text)
            words = normalized.split()
            if len(words) < 4:
                continue
            if len(words) > 42:
                statement_text = " ".join(statement_text.split()[:42])
                normalized = module.normalize(statement_text)
                words = normalized.split()
            text_tokens = module.meaningful_tokens(statement_text)
            overlap = text_tokens & context_tokens
            phrase_hits = [hint for hint in hints if len(module.normalize(hint)) >= 5 and module.normalize(hint) in normalized]
            anchor_hits = text_tokens & TRUTH_ANCHORS

            if seed.get("verdict") == "lie":
                qualified = bool(phrase_hits) or len(overlap & hint_tokens) >= 2
            else:
                qualified = (
                    len(overlap & hint_tokens) >= 2
                    or (len(overlap) >= 2 and bool(anchor_hits))
                    or (len(overlap) >= 1 and len(anchor_hits) >= 2)
                )
            if not qualified:
                continue

            score = len(overlap & hint_tokens) * 3 + len(overlap) + len(phrase_hits) * 5 + min(3, len(anchor_hits))
            if 5 <= len(words) <= 30:
                score += 2
            candidate = {
                "score": float(score),
                "text": statement_text,
                "start": segments[left]["start"],
                "end": segments[right]["start"] + segments[right]["duration"],
                "details": {
                    "hintTokens": sorted(hint_tokens),
                    "overlap": sorted(overlap),
                    "phraseHits": phrase_hits,
                    "firstPerson": True,
                    "wordCount": len(words),
                    "anchorHits": sorted(anchor_hits),
                },
            }
            if best is None or candidate["score"] > best["score"]:
                best = candidate
    return best


def evaluate_cached(seed: dict[str, Any], cached: dict[str, Any]) -> dict[str, Any] | None:
    candidate = {
        "videoId": cached.get("videoId"),
        "title": cached.get("title"),
        "channel": cached.get("channel"),
        "duration": cached.get("duration"),
    }
    if not candidate["videoId"] or not candidate["title"]:
        return None
    return module.evaluate_video(seed, candidate)


def process_seed(seed: dict[str, Any]) -> dict[str, Any]:
    seed_id = str(seed.get("seedId"))
    attempts: list[dict[str, Any]] = []
    seen: set[str] = set()
    checked = 0

    for cached in cached_by_seed.get(seed_id, []):
        video_id = str(cached.get("videoId") or "")
        if not video_id or video_id in seen:
            continue
        seen.add(video_id)
        checked += 1
        evaluated = evaluate_cached(seed, cached)
        if evaluated:
            return {"seed": seed, "attempts": [{"source": "method-v5 cache"}], "candidates": [evaluated], "checkedCandidates": checked}

    for query in list(seed.get("searchQueries") or [])[:2]:
        search_results = module.youtube_search(str(query))
        attempts.append({"query": query, "resultCount": len(search_results)})
        for candidate in search_results[:12]:
            video_id = candidate["videoId"]
            if video_id in seen:
                continue
            seen.add(video_id)
            checked += 1
            evaluated = module.evaluate_video(seed, candidate)
            if evaluated:
                return {"seed": seed, "attempts": attempts, "candidates": [evaluated], "checkedCandidates": checked}
    return {"seed": seed, "attempts": attempts, "candidates": [], "checkedCandidates": checked}


module.timed_transcript = timed_transcript
module.youtube_public_metadata = public_metadata
module.extract_statement = precise_extract_statement
module.process_seed = process_seed
module.SEARCH_WORKERS = 12
exit_code = module.main()

if module.REPORT_PATH.exists():
    report = json.loads(module.REPORT_PATH.read_text(encoding="utf-8"))
    report["methodVersion"] = 6
    report["transcriptProvider"] = "Confirmed YouTube2Text POST {url} timed segments"
    report["strategy"] = "Revalidate method-v5 sources, isolate first-person quote, then search up to 12 results for missing seeds"
    module.REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

raise SystemExit(exit_code)
