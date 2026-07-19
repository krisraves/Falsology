#!/usr/bin/env python3
from __future__ import annotations

import concurrent.futures
import json
import re
import subprocess
import unicodedata
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
EXACT = ROOT / "data" / "exact-statement-overrides.json"
ACTIVE = ROOT / "data" / "active-case-numbers.json"
DIFFICULTY = ROOT / "data" / "difficulty-map.json"
OUTPUT = ROOT / "data" / "research" / "archive-source-recovery.json"
OVERRIDES_OUTPUT = ROOT / "data" / "recovered-archive-overrides.json"
TRANSCRIPT_ENDPOINT = "https://youtube2text.diguardia.org/api/transcript"
HEADERS = {"user-agent": "Mozilla/5.0 Chrome/126 Safari/537.36"}
REJECT_TITLE = re.compile(r"\b(reaction|reacts|analysis|explained|body language|compilation|shorts|breakdown)\b", re.I)


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def search(query: str) -> list[dict[str, Any]]:
    cmd = ["yt-dlp", "--flat-playlist", "--dump-json", "--no-warnings", "--ignore-errors", f"ytsearch20:{query}"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=110, check=False)
    except subprocess.TimeoutExpired:
        return []
    values: list[dict[str, Any]] = []
    for line in result.stdout.splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        video_id = str(item.get("id", ""))
        if len(video_id) != 11:
            continue
        values.append({
            "videoId": video_id,
            "title": str(item.get("title") or ""),
            "channel": str(item.get("channel") or item.get("uploader") or "Unknown channel"),
        })
    return values


def transcript(video_id: str) -> list[dict[str, Any]]:
    try:
        response = requests.post(
            TRANSCRIPT_ENDPOINT,
            json={"url": f"https://www.youtube.com/watch?v={video_id}"},
            headers=HEADERS,
            timeout=55,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return []
    candidates = payload.get("segments") or payload.get("transcript") or payload.get("data") or payload
    if isinstance(candidates, dict):
        candidates = candidates.get("segments") or candidates.get("transcript") or []
    if not isinstance(candidates, list):
        return []
    output: list[dict[str, Any]] = []
    for segment in candidates:
        if not isinstance(segment, dict):
            continue
        text = str(segment.get("text") or segment.get("content") or "").strip()
        start = segment.get("start")
        duration = segment.get("duration")
        if duration is None and segment.get("end") is not None and start is not None:
            duration = float(segment["end"]) - float(start)
        try:
            start_number = float(start)
            duration_number = max(0.05, float(duration or 0.1))
        except (TypeError, ValueError):
            continue
        if text:
            output.append({"text": text, "start": start_number, "duration": duration_number})
    output.sort(key=lambda item: item["start"])
    return output


def find_exact(segments: list[dict[str, Any]], claim: str) -> dict[str, Any] | None:
    target = normalize(claim)
    if len(target) < 8:
        return None
    for left in range(len(segments)):
        text_parts: list[str] = []
        for right in range(left, min(len(segments), left + 16)):
            text_parts.append(segments[right]["text"])
            joined = " ".join(text_parts)
            normalized = normalize(joined)
            if target in normalized:
                # Trim preceding/following transcript captions where possible while
                # preserving the complete exact statement.
                start = segments[left]["start"]
                end = segments[right]["start"] + segments[right]["duration"]
                return {"start": start, "end": end, "spokenText": joined}
            if len(normalized) > len(target) * 4 + 180:
                break
    return None


def public_and_embeddable(video_id: str) -> bool:
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        response = requests.get(url, headers=HEADERS, timeout=25)
        if response.status_code != 200:
            return False
        embed = requests.get(f"https://www.youtube.com/embed/{video_id}?hl=en", headers=HEADERS, timeout=25)
        return embed.status_code < 400
    except Exception:
        return False


def query_variants(person: str, claim: str) -> list[str]:
    tokens = normalize(claim).split()
    compact = " ".join(tokens[:10])
    variants = [
        f'"{claim}" "{person}"',
        f'"{claim}" {person} interview',
        f'{person} "{compact}" interview testimony statement',
        f'{person} {compact} full video',
    ]
    seen: set[str] = set()
    return [query for query in variants if not (query in seen or seen.add(query))]


def recover(case_number: str, item: dict[str, Any], forbidden_ids: set[str]) -> dict[str, Any]:
    person = str(item.get("person") or "")
    claim = str(item.get("claim") or "")
    current_id = str(item.get("media", {}).get("youtubeId") or "")
    attempts: list[dict[str, Any]] = []
    checked: set[str] = set()
    subject_tokens = [token for token in normalize(person).split() if len(token) > 2]

    for query in query_variants(person, claim):
        results = search(query)
        attempts.append({"query": query, "resultCount": len(results)})
        for candidate in results:
            video_id = candidate["videoId"]
            if video_id in checked:
                continue
            checked.add(video_id)
            if video_id in forbidden_ids or video_id == current_id:
                continue
            title = candidate["title"]
            if REJECT_TITLE.search(title):
                attempts.append({"videoId": video_id, "reason": "rejected packaging"})
                continue
            title_and_channel = normalize(f"{title} {candidate['channel']}")
            if subject_tokens and not any(token in title_and_channel for token in subject_tokens):
                attempts.append({"videoId": video_id, "reason": "speaker not identified by title or channel"})
                continue
            if not public_and_embeddable(video_id):
                attempts.append({"videoId": video_id, "reason": "not public or embeddable"})
                continue
            segments = transcript(video_id)
            if not segments:
                attempts.append({"videoId": video_id, "reason": "no timed transcript"})
                continue
            exact = find_exact(segments, claim)
            if not exact:
                attempts.append({"videoId": video_id, "reason": "exact statement absent"})
                continue
            duration = max(segment["start"] + segment["duration"] for segment in segments)
            start = max(0, round(exact["start"] - 5, 2))
            end = min(duration, round(exact["end"] + 5, 2))
            return {
                "caseNumber": case_number,
                "status": "recovered",
                "person": person,
                "claim": claim,
                "verdict": item.get("verdict"),
                "difficulty": difficulties.get(case_number),
                "media": {
                    "type": "youtube",
                    "youtubeId": video_id,
                    "startSeconds": start,
                    "endSeconds": end,
                    "statementStartSeconds": round(exact["start"], 2),
                    "statementEndSeconds": round(exact["end"], 2),
                    "spokenText": exact["spokenText"],
                    "videoDurationSeconds": round(duration, 2),
                    "url": f"https://www.youtube.com/watch?v={video_id}&t={start}s",
                    "label": "Open the complete source recording",
                    "verifiedAt": "2026-07-19",
                    "sourceKind": "direct-interview",
                    "directStatement": True,
                    "newsPackage": False,
                    "sourceTitle": title,
                    "sourceChannel": candidate["channel"],
                },
                "attempts": attempts,
            }
    return {
        "caseNumber": case_number,
        "status": "unresolved",
        "person": person,
        "claim": claim,
        "verdict": item.get("verdict"),
        "difficulty": difficulties.get(case_number),
        "attempts": attempts,
    }


exact = json.loads(EXACT.read_text())
active = json.loads(ACTIVE.read_text())
difficulties = json.loads(DIFFICULTY.read_text())
active_ids = {exact[number]["media"]["youtubeId"] for number in active}
remaining = [(number, item) for number, item in exact.items() if number not in set(active)]

results: list[dict[str, Any]] = []
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    futures = {executor.submit(recover, number, item, active_ids.copy()): number for number, item in remaining}
    for future in concurrent.futures.as_completed(futures):
        result = future.result()
        results.append(result)
        print(f'{result["caseNumber"]}: {result["status"]}', flush=True)

# Deduplicate recovered results deterministically, preserving the lowest case number.
seen = set(active_ids)
for result in sorted(results, key=lambda item: item["caseNumber"]):
    if result["status"] != "recovered":
        continue
    video_id = result["media"]["youtubeId"]
    if video_id in seen:
        result["status"] = "unresolved"
        result["attempts"].append({"videoId": video_id, "reason": "duplicate recovered source"})
        result.pop("media", None)
    else:
        seen.add(video_id)

summary: dict[str, Any] = {"recovered": 0, "unresolved": 0, "byDifficulty": {}}
overrides: dict[str, Any] = {}
for result in results:
    summary[result["status"]] += 1
    difficulty = result.get("difficulty") or "unknown"
    summary["byDifficulty"].setdefault(difficulty, {"recovered": 0, "unresolved": 0})
    summary["byDifficulty"][difficulty][result["status"]] += 1
    if result["status"] == "recovered":
        overrides[result["caseNumber"]] = {"media": result["media"]}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps({"methodVersion": 2, "summary": summary, "results": sorted(results, key=lambda item: item["caseNumber"])}, indent=2) + "\n")
OVERRIDES_OUTPUT.write_text(json.dumps(overrides, indent=2) + "\n")
print(json.dumps(summary, indent=2))
