#!/usr/bin/env python3
"""Restore historical candidates, improve truth extraction, and fill quotas."""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests

SCRIPT = Path(__file__).with_name("build-verified-content-deck.py")
spec = importlib.util.spec_from_file_location("falsology_builder_v7", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load content builder")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

cached_by_seed: dict[str, list[dict[str, Any]]] = defaultdict(list)
for report_path in [module.ROOT / "data/research/content-build-report-v4.json", module.REPORT_PATH]:
    if not report_path.exists():
        continue
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception:
        continue
    for result in report.get("seedResults", []):
        seed_id = str(result.get("seed", {}).get("seedId") or "")
        for candidate in result.get("candidates") or []:
            video_id = str(candidate.get("videoId") or "")
            if seed_id and video_id and all(str(value.get("videoId")) != video_id for value in cached_by_seed[seed_id]):
                cached_by_seed[seed_id].append(candidate)

TRUTH_ANCHORS = {
    "innocent", "prison", "jail", "years", "months", "days", "hours", "dna", "exonerated",
    "convicted", "wrongfully", "released", "freed", "survived", "trapped", "captive", "kidnapped",
    "escaped", "warned", "exposed", "ocean", "sea", "mountain", "plane", "radiation", "avalanche",
    "explosion", "crash", "mine", "hostage", "alive", "confession", "recanted", "fingerprints",
}
NEGATION = re.compile(r"\b(no|not|never|didn't|didnt|wasn't|wasnt|isn't|isnt|couldn't|couldnt)\b", re.I)


def parse_segments(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        payload = payload.get("segments") or payload.get("transcript") or payload.get("data") or []
        if isinstance(payload, dict):
            payload = payload.get("segments") or payload.get("transcript") or payload.get("data") or []
    if not isinstance(payload, list):
        return []
    output = []
    for raw in payload:
        if not isinstance(raw, dict):
            continue
        text = str(raw.get("text") or raw.get("content") or "").strip()
        try:
            start = float(raw.get("start"))
            duration = max(0.05, float(raw.get("duration") or (float(raw.get("end")) - start)))
        except (TypeError, ValueError):
            continue
        if text:
            output.append({"text": text, "start": start, "duration": duration})
    output.sort(key=lambda value: value["start"])
    return output


def timed_transcript(video_id: str) -> list[dict[str, Any]]:
    try:
        response = requests.post(
            module.TRANSCRIPT_ENDPOINT,
            json={"url": f"https://www.youtube.com/watch?v={video_id}"},
            headers=module.HEADERS,
            timeout=32,
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
            timeout=18,
        )
        if response.status_code != 200:
            return None
        data = response.json()
        return {"title": str(data.get("title") or ""), "channel": str(data.get("author_name") or "YouTube source channel"), "embeddable": True}
    except Exception:
        return None


def extract_statement(segments: list[dict[str, Any]], seed: dict[str, Any]) -> dict[str, Any] | None:
    hints = [str(value) for value in seed.get("statementHints", []) if str(value).strip()]
    hint_tokens = set().union(*(module.meaningful_tokens(value) for value in hints)) if hints else set()
    context_tokens = hint_tokens | module.meaningful_tokens(str(seed.get("factSummary") or "")) | module.meaningful_tokens(str(seed.get("evidenceQuery") or ""))
    best = None
    for left in range(len(segments)):
        parts = []
        for right in range(left, min(len(segments), left + 10)):
            parts.append(segments[right]["text"])
            raw = re.sub(r"\s+", " ", " ".join(parts)).strip()
            marker = module.FIRST_PERSON.search(raw)
            if not marker or len(module.normalize(raw[: marker.start()]).split()) > 10:
                continue
            statement = raw[marker.start() :].strip(" -:,.\"")
            normalized = module.normalize(statement)
            words = normalized.split()
            if len(words) < 4:
                continue
            if len(words) > 40:
                statement = " ".join(statement.split()[:40])
                normalized = module.normalize(statement)
                words = normalized.split()
            if module.QUESTION_CUES.search(normalized):
                continue
            text_tokens = module.meaningful_tokens(statement)
            hint_overlap = text_tokens & hint_tokens
            context_overlap = text_tokens & context_tokens
            phrase_hits = [hint for hint in hints if len(module.normalize(hint)) >= 5 and module.normalize(hint) in normalized]
            anchors = text_tokens & TRUTH_ANCHORS
            has_number = bool(re.search(r"\b\d+\b", normalized))
            if seed.get("verdict") == "lie":
                qualified = bool(phrase_hits) or len(hint_overlap) >= 2 or (len(context_overlap) >= 3 and bool(NEGATION.search(statement)))
            else:
                qualified = len(hint_overlap) >= 2 or len(anchors) >= 2 or (bool(hint_overlap) and bool(anchors)) or len(context_overlap) >= 2 or (has_number and bool(hint_overlap | anchors))
            if not qualified:
                continue
            score = len(hint_overlap) * 4 + len(context_overlap) + len(phrase_hits) * 6 + min(5, len(anchors)) + (2 if has_number else 0)
            if 5 <= len(words) <= 28:
                score += 3
            if seed.get("verdict") == "lie" and NEGATION.search(statement):
                score += 2
            candidate = {
                "score": float(score),
                "text": statement,
                "start": segments[left]["start"],
                "end": segments[right]["start"] + segments[right]["duration"],
                "details": {"hintTokens": sorted(hint_tokens), "overlap": sorted(context_overlap), "phraseHits": phrase_hits, "firstPerson": True, "wordCount": len(words), "anchorHits": sorted(anchors), "hasNumber": has_number},
            }
            if best is None or candidate["score"] > best["score"]:
                best = candidate
    return best


def process_seed(seed: dict[str, Any]) -> dict[str, Any]:
    seed_id = str(seed.get("seedId"))
    attempts = []
    seen = set()
    checked = 0
    for cached in cached_by_seed.get(seed_id, []):
        video_id = str(cached.get("videoId") or "")
        if not video_id or video_id in seen:
            continue
        seen.add(video_id)
        checked += 1
        candidate = {"videoId": video_id, "title": cached.get("title"), "channel": cached.get("channel"), "duration": cached.get("duration")}
        if candidate["title"]:
            evaluated = module.evaluate_video(seed, candidate)
            if evaluated:
                return {"seed": seed, "attempts": [{"source": "restored candidate history"}], "candidates": [evaluated], "checkedCandidates": checked}
    for query in list(seed.get("searchQueries") or [])[:3]:
        results = module.youtube_search(str(query))
        attempts.append({"query": query, "resultCount": len(results)})
        for candidate in results[:20]:
            video_id = candidate["videoId"]
            if video_id in seen:
                continue
            seen.add(video_id)
            checked += 1
            evaluated = module.evaluate_video(seed, candidate)
            if evaluated:
                return {"seed": seed, "attempts": attempts, "candidates": [evaluated], "checkedCandidates": checked}
    return {"seed": seed, "attempts": attempts, "candidates": [], "checkedCandidates": checked}


def select_cases(processed, existing_ids, required):
    pools = defaultdict(list)
    by_verdict = defaultdict(list)
    for result in processed:
        seed = result["seed"]
        for candidate in result["candidates"]:
            option = {"seed": seed, "candidate": candidate}
            pools[(seed["difficulty"], seed["verdict"])].append(option)
            by_verdict[seed["verdict"]].append(option)
    for values in list(pools.values()) + list(by_verdict.values()):
        values.sort(key=lambda item: item["candidate"]["confidence"], reverse=True)
    used_ids = set(existing_ids)
    used_seeds = set()
    selected = []
    counts = defaultdict(int)
    for difficulty in ("easy", "medium", "hard"):
        for verdict in ("truth", "lie"):
            key = (difficulty, verdict)
            for option in pools.get(key, []):
                seed_id = str(option["seed"]["seedId"])
                video_id = str(option["candidate"]["videoId"])
                if seed_id in used_seeds or video_id in used_ids:
                    continue
                used_seeds.add(seed_id); used_ids.add(video_id); selected.append(option); counts[key] += 1
                if counts[key] >= required[key]:
                    break
    order = {"easy": 0, "medium": 1, "hard": 2}
    for verdict in ("truth", "lie"):
        for target in ("easy", "medium", "hard"):
            key = (target, verdict)
            need = required[key] - counts[key]
            if need <= 0:
                continue
            options = sorted(by_verdict.get(verdict, []), key=lambda item: (abs(order[item["seed"]["difficulty"]] - order[target]), -item["candidate"]["confidence"]))
            for option in options:
                seed_id = str(option["seed"]["seedId"]); video_id = str(option["candidate"]["videoId"])
                if seed_id in used_seeds or video_id in used_ids:
                    continue
                selected.append({"seed": {**option["seed"], "difficulty": target}, "candidate": option["candidate"]})
                used_seeds.add(seed_id); used_ids.add(video_id); counts[key] += 1; need -= 1
                if need <= 0:
                    break
    shortfalls = {}
    for difficulty in ("easy", "medium", "hard"):
        for verdict in ("truth", "lie"):
            key = (difficulty, verdict)
            if counts[key] < required[key]:
                shortfalls[f"{difficulty}:{verdict}"] = {"required": required[key], "selected": counts[key], "availableOptions": len(by_verdict.get(verdict, []))}
    return selected, shortfalls

module.timed_transcript = timed_transcript
module.youtube_public_metadata = public_metadata
module.extract_statement = extract_statement
module.process_seed = process_seed
module.select_cases = select_cases
module.MAX_RESULTS_PER_QUERY = 20
module.SEARCH_WORKERS = 12
exit_code = module.main()
if module.REPORT_PATH.exists():
    report = json.loads(module.REPORT_PATH.read_text(encoding="utf-8"))
    report["methodVersion"] = 7
    report["transcriptProvider"] = "YouTube2Text POST URL timed segments"
    report["strategy"] = "Restore historical candidates, improve truth extraction, and rebalance difficulty"
    module.REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
raise SystemExit(exit_code)
