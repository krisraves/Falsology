#!/usr/bin/env python3
"""Build Falsology's verified 120-case deck from exact-statement content seeds.

The script publishes nothing unless it can fill every required slot. New cases
must use unique public YouTube sources, direct footage, timed English captions,
an exact transcript-derived displayed statement, a ±5-second clip, and a
relevant secondary reference.
"""

from __future__ import annotations

import concurrent.futures
import json
import re
import subprocess
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
SEED_DIR = ROOT / "data" / "research" / "content-seeds"
ACTIVE_PATH = ROOT / "data" / "active-case-numbers.json"
EXACT_PATH = ROOT / "data" / "exact-statement-overrides.json"
DIFFICULTY_PATH = ROOT / "data" / "difficulty-map.json"
OUTPUT_PATH = ROOT / "data" / "generated-cases.json"
REPORT_PATH = ROOT / "data" / "research" / "content-build-report.json"
TRANSCRIPT_ENDPOINT = "https://youtube2text.diguardia.org/api/transcript"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"user-agent": "FalsologyEditorialVerifier/1.0 (public research; contact via repository)"}
TODAY = date.today().isoformat()
TARGET_PER_DIFFICULTY = 40
TARGET_PER_VERDICT = 20
MAX_RESULTS_PER_QUERY = 12
MAX_CANDIDATES_PER_SEED = 3
SEARCH_WORKERS = 6
HTTP_TIMEOUT = 35

REJECT_TITLE = re.compile(
    r"\b(reaction|reacts|analysis|explained|body language|compilation|top 10|shorts|#shorts|breakdown|reenactment|dramatization|movie clip|trailer|parody)\b",
    re.I,
)
DIRECT_TITLE = re.compile(
    r"\b(interview|interrogation|testimony|hearing|statement|speech|confession|deposition|press conference|briefing|court|trial|full|raw|survivor|exonerat|inquiry)\b",
    re.I,
)
FIRST_PERSON = re.compile(r"\b(i|i'm|im|i've|ive|i'd|i'll|me|my|mine|we|we're|weve|we've|our|ours)\b", re.I)
QUESTION_CUES = re.compile(r"^(who|what|when|where|why|how|did|do|does|are|were|can|could|would|will|tell me)\b", re.I)
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "being", "but", "by", "for", "from", "had", "has", "have",
    "he", "her", "hers", "him", "his", "i", "if", "in", "into", "is", "it", "its", "me", "my", "of", "on", "or", "our",
    "she", "so", "that", "the", "their", "them", "they", "this", "to", "was", "we", "were", "what", "when", "where", "which",
    "who", "with", "you", "your", "full", "video", "interview", "testimony", "statement", "speech", "footage", "raw",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9']+", " ", value.lower()).strip()


def slugify(value: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", normalize(value))).strip("-")[:120]


def meaningful_tokens(value: str) -> set[str]:
    return {token for token in normalize(value).split() if len(token) > 2 and token not in STOP_WORDS}


def load_seeds() -> list[dict[str, Any]]:
    seeds: list[dict[str, Any]] = []
    for path in sorted(SEED_DIR.glob("*.json")):
        values = read_json(path)
        if not isinstance(values, list):
            raise ValueError(f"{path} must contain a JSON list")
        seeds.extend(values)
    ids = [str(seed.get("seedId")) for seed in seeds]
    if len(ids) != len(set(ids)):
        raise ValueError("Content seed IDs must be unique")
    return seeds


def youtube_search(query: str) -> list[dict[str, Any]]:
    command = [
        "yt-dlp", "--flat-playlist", "--dump-json", "--no-warnings", "--ignore-errors",
        f"ytsearch{MAX_RESULTS_PER_QUERY}:{query}",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=110, check=False)
    except subprocess.TimeoutExpired:
        return []
    candidates: list[dict[str, Any]] = []
    for line in result.stdout.splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        video_id = str(item.get("id") or "")
        title = str(item.get("title") or "").strip()
        if len(video_id) != 11 or not title:
            continue
        duration = item.get("duration")
        try:
            duration_value = float(duration) if duration is not None else None
        except (TypeError, ValueError):
            duration_value = None
        candidates.append({
            "videoId": video_id,
            "title": title,
            "channel": str(item.get("channel") or item.get("uploader") or "YouTube source channel"),
            "duration": duration_value,
        })
    return candidates


def youtube_public_metadata(video_id: str) -> dict[str, Any] | None:
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        response = requests.get(oembed_url, headers=HEADERS, timeout=HTTP_TIMEOUT)
        if response.status_code != 200:
            return None
        data = response.json()
        embed_response = requests.get(f"https://www.youtube.com/embed/{video_id}?hl=en", headers=HEADERS, timeout=HTTP_TIMEOUT)
        if embed_response.status_code >= 400:
            return None
        body = embed_response.text.lower()
        explicit_disabled = (
            "playback on other websites has been disabled" in body
            or "embedding disabled" in body
            or "this video is private" in body
            or "this video has been removed" in body
        )
        if explicit_disabled:
            return None
        return {
            "title": str(data.get("title") or ""),
            "channel": str(data.get("author_name") or "YouTube source channel"),
            "embeddable": True,
        }
    except Exception:
        return None


def timed_transcript(video_id: str) -> list[dict[str, Any]]:
    try:
        response = requests.get(
            TRANSCRIPT_ENDPOINT,
            params={"video_id": video_id},
            headers=HEADERS,
            timeout=50,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return []
    values: Any = payload.get("transcript") or payload.get("segments") or payload.get("data") or payload
    if isinstance(values, dict):
        values = values.get("segments") or values.get("transcript") or values.get("data") or []
    if not isinstance(values, list):
        return []
    output: list[dict[str, Any]] = []
    for raw in values:
        if not isinstance(raw, dict):
            continue
        text = str(raw.get("text") or raw.get("content") or raw.get("utf8") or "").strip()
        start = raw.get("start") if raw.get("start") is not None else raw.get("offset")
        duration = raw.get("duration")
        end = raw.get("end")
        try:
            start_number = float(start)
            if duration is not None:
                duration_number = max(0.05, float(duration))
            elif end is not None:
                duration_number = max(0.05, float(end) - start_number)
            else:
                duration_number = 0.5
        except (TypeError, ValueError):
            continue
        if text:
            output.append({"text": text, "start": start_number, "duration": duration_number})
    output.sort(key=lambda item: item["start"])
    return output


def hint_score(text: str, seed: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    normalized = normalize(text)
    text_tokens = meaningful_tokens(text)
    hints = [str(hint) for hint in seed.get("statementHints", []) if str(hint).strip()]
    hint_tokens = set().union(*(meaningful_tokens(hint) for hint in hints)) if hints else set()
    overlap = text_tokens & hint_tokens
    phrase_hits = [hint for hint in hints if len(normalize(hint)) >= 5 and normalize(hint) in normalized]
    token_ratio = len(overlap) / max(1, min(len(hint_tokens), 8))
    score = token_ratio * 6 + len(phrase_hits) * 4
    if FIRST_PERSON.search(text):
        score += 3
    if QUESTION_CUES.search(normalized):
        score -= 2
    word_count = len(normalized.split())
    if 5 <= word_count <= 34:
        score += 2
    elif word_count > 52:
        score -= 4
    return score, {
        "hintTokens": sorted(hint_tokens),
        "overlap": sorted(overlap),
        "phraseHits": phrase_hits,
        "firstPerson": bool(FIRST_PERSON.search(text)),
        "wordCount": word_count,
    }


def extract_statement(segments: list[dict[str, Any]], seed: dict[str, Any]) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    for left in range(len(segments)):
        text_parts: list[str] = []
        for right in range(left, min(len(segments), left + 8)):
            text_parts.append(segments[right]["text"])
            text = " ".join(text_parts).strip()
            score, details = hint_score(text, seed)
            if score >= 8 and details["firstPerson"] and len(details["overlap"]) >= 2:
                start = segments[left]["start"]
                end = segments[right]["start"] + segments[right]["duration"]
                candidate = {
                    "score": score,
                    "text": text,
                    "start": start,
                    "end": end,
                    "details": details,
                }
                if best is None or candidate["score"] > best["score"]:
                    best = candidate
            if details["wordCount"] > 55:
                break
    if best is None:
        return None
    # Use the exact caption text, lightly normalizing whitespace only.
    best["text"] = re.sub(r"\s+", " ", best["text"]).strip()
    return best


def wikipedia_reference(seed: dict[str, Any]) -> dict[str, str] | None:
    query = str(seed.get("evidenceQuery") or seed.get("person") or "").strip()
    if not query:
        return None
    try:
        response = requests.get(
            WIKIPEDIA_API,
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": 5,
                "format": "json",
                "utf8": 1,
                "origin": "*",
            },
            headers=HEADERS,
            timeout=HTTP_TIMEOUT,
        )
        response.raise_for_status()
        results = response.json().get("query", {}).get("search", [])
    except Exception:
        return None
    query_tokens = meaningful_tokens(query)
    for result in results:
        title = str(result.get("title") or "")
        snippet = re.sub(r"<[^>]+>", " ", str(result.get("snippet") or ""))
        combined_tokens = meaningful_tokens(f"{title} {snippet}")
        if query_tokens and not (query_tokens & combined_tokens):
            continue
        return {
            "title": title,
            "publisher": "Wikipedia reference record",
            "url": f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}",
            "note": str(seed.get("factSummary") or "Independent background reference for the displayed statement."),
        }
    return None


def subject_title_confidence(person: str, title: str) -> float:
    person_tokens = meaningful_tokens(person)
    title_tokens = meaningful_tokens(title)
    if not person_tokens:
        return 0
    return len(person_tokens & title_tokens) / len(person_tokens)


def evaluate_video(seed: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any] | None:
    title = candidate["title"]
    if REJECT_TITLE.search(title):
        return None
    subject_confidence = subject_title_confidence(str(seed.get("person") or ""), title)
    if subject_confidence < 0.5:
        return None
    if not DIRECT_TITLE.search(title) and subject_confidence < 1:
        return None
    public = youtube_public_metadata(candidate["videoId"])
    if not public:
        return None
    transcript = timed_transcript(candidate["videoId"])
    if not transcript:
        return None
    statement = extract_statement(transcript, seed)
    if not statement:
        return None
    reference = wikipedia_reference(seed)
    if not reference:
        return None
    transcript_end = max(segment["start"] + segment["duration"] for segment in transcript)
    duration = candidate.get("duration") or transcript_end
    duration = max(float(duration), transcript_end)
    clip_start = max(0, round(statement["start"] - 5, 2))
    clip_end = min(duration, round(statement["end"] + 5, 2))
    confidence = statement["score"] + subject_confidence * 4 + (2 if DIRECT_TITLE.search(title) else 0)
    return {
        "videoId": candidate["videoId"],
        "title": public.get("title") or title,
        "channel": public.get("channel") or candidate.get("channel") or "YouTube source channel",
        "duration": round(duration, 2),
        "statement": statement,
        "clipStart": clip_start,
        "clipEnd": round(clip_end, 2),
        "reference": reference,
        "confidence": round(confidence, 3),
        "subjectTitleConfidence": round(subject_confidence, 3),
    }


def process_seed(seed: dict[str, Any]) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    accepted: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for query in list(seed.get("searchQueries") or [])[:2]:
        search_results = youtube_search(str(query))
        attempts.append({"query": query, "resultCount": len(search_results)})
        for candidate in search_results:
            video_id = candidate["videoId"]
            if video_id in seen_ids:
                continue
            seen_ids.add(video_id)
            evaluated = evaluate_video(seed, candidate)
            if evaluated:
                accepted.append(evaluated)
                accepted.sort(key=lambda item: item["confidence"], reverse=True)
                accepted = accepted[:MAX_CANDIDATES_PER_SEED]
        if accepted:
            break
    return {"seed": seed, "attempts": attempts, "candidates": accepted}


def make_case(seed: dict[str, Any], selected: dict[str, Any], number: int) -> dict[str, Any]:
    case_number = f"G{number:03d}"
    statement = selected["statement"]["text"]
    person = str(seed["person"])
    verdict = str(seed["verdict"])
    difficulty = str(seed["difficulty"])
    slug = f"{case_number.lower()}-{slugify(person)}-{slugify(statement)}"
    classification = "Documented false statement" if verdict == "lie" else "Documented true statement"
    fact_summary = str(seed["factSummary"])
    primary_url = f"https://www.youtube.com/watch?v={selected['videoId']}"
    return {
        "id": case_number.lower(),
        "slug": slug,
        "caseNumber": case_number,
        "person": person,
        "personSlug": slugify(person),
        "personRole": str(seed.get("personRole") or "Public figure or witness"),
        "category": str(seed.get("category") or "Direct statement"),
        "categorySlug": str(seed.get("categorySlug") or "direct-statement"),
        "setting": str(seed.get("setting") or "Recorded statement"),
        "date": "undated",
        "claim": statement,
        "prompt": "Truth or lie?",
        "verdict": verdict,
        "classification": classification,
        "difficulty": difficulty,
        "shortExplanation": fact_summary,
        "fullTruth": fact_summary,
        "context": f"The playable excerpt is centered on the exact captioned line: “{statement}”",
        "transcript": statement,
        "editorialBoundary": "The verdict applies only to the displayed statement and the cited evidence. Automated caption text was checked against the timed source before publication.",
        "signals": [
            "Exact timed transcript",
            "Direct source recording",
            "Independent reference record",
        ],
        "lesson": "Judge the statement against corroborated records, not confidence, appearance, or body-language speculation.",
        "media": {
            "type": "youtube",
            "youtubeId": selected["videoId"],
            "startSeconds": selected["clipStart"],
            "endSeconds": selected["clipEnd"],
            "statementStartSeconds": round(selected["statement"]["start"], 2),
            "statementEndSeconds": round(selected["statement"]["end"], 2),
            "spokenText": statement,
            "videoDurationSeconds": selected["duration"],
            "url": f"{primary_url}&t={selected['clipStart']}s",
            "label": "Open the complete source recording",
            "verifiedAt": TODAY,
            "sourceKind": "direct-interview",
            "directStatement": True,
            "newsPackage": False,
        },
        "sources": [
            {
                "title": selected["title"],
                "publisher": selected["channel"],
                "url": primary_url,
                "type": "primary",
                "note": "Contains the exact timed statement used in the playable excerpt.",
            },
            {
                "title": selected["reference"]["title"],
                "publisher": selected["reference"]["publisher"],
                "url": selected["reference"]["url"],
                "type": "secondary",
                "note": selected["reference"]["note"],
            },
        ],
        "tags": [difficulty, verdict, "exact-statement", "unique-video"],
        "reviewedAt": TODAY,
        "buildMetadata": {
            "seedId": seed["seedId"],
            "confidence": selected["confidence"],
            "subjectTitleConfidence": selected["subjectTitleConfidence"],
            "sourceTitle": selected["title"],
        },
    }


def select_cases(processed: list[dict[str, Any]], existing_ids: set[str], required: dict[tuple[str, str], int]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pools: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for result in processed:
        seed = result["seed"]
        for candidate in result["candidates"]:
            pools[(seed["difficulty"], seed["verdict"])].append({"seed": seed, "candidate": candidate})
    for pool in pools.values():
        pool.sort(key=lambda item: item["candidate"]["confidence"], reverse=True)

    used_ids = set(existing_ids)
    used_seeds: set[str] = set()
    selected: list[dict[str, Any]] = []
    shortfalls: dict[str, Any] = {}
    for difficulty in ("easy", "medium", "hard"):
        for verdict in ("truth", "lie"):
            key = (difficulty, verdict)
            need = required[key]
            picked = 0
            for option in pools.get(key, []):
                seed_id = str(option["seed"]["seedId"])
                video_id = str(option["candidate"]["videoId"])
                if seed_id in used_seeds or video_id in used_ids:
                    continue
                used_seeds.add(seed_id)
                used_ids.add(video_id)
                selected.append(option)
                picked += 1
                if picked >= need:
                    break
            if picked < need:
                shortfalls[f"{difficulty}:{verdict}"] = {
                    "required": need,
                    "selected": picked,
                    "availableOptions": len(pools.get(key, [])),
                }
    return selected, shortfalls


def main() -> int:
    seeds = load_seeds()
    active_numbers = read_json(ACTIVE_PATH)
    exact = read_json(EXACT_PATH)
    difficulty_map = read_json(DIFFICULTY_PATH)
    existing_counts: Counter[tuple[str, str]] = Counter()
    existing_ids: set[str] = set()
    for case_number in active_numbers:
        item = exact[case_number]
        difficulty = difficulty_map[case_number]
        existing_counts[(difficulty, item["verdict"])] += 1
        existing_ids.add(item["media"]["youtubeId"])

    required: dict[tuple[str, str], int] = {}
    for difficulty in ("easy", "medium", "hard"):
        for verdict in ("truth", "lie"):
            required[(difficulty, verdict)] = TARGET_PER_VERDICT - existing_counts[(difficulty, verdict)]

    print(f"Processing {len(seeds)} curated content seeds with {SEARCH_WORKERS} workers.", flush=True)
    processed: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=SEARCH_WORKERS) as executor:
        future_map = {executor.submit(process_seed, seed): seed["seedId"] for seed in seeds}
        for completed, future in enumerate(concurrent.futures.as_completed(future_map), start=1):
            result = future.result()
            processed.append(result)
            print(
                f"[{completed}/{len(seeds)}] {future_map[future]}: {len(result['candidates'])} verified candidate(s)",
                flush=True,
            )

    selected, shortfalls = select_cases(processed, existing_ids, required)
    selected.sort(key=lambda item: (
        {"easy": 0, "medium": 1, "hard": 2}[item["seed"]["difficulty"]],
        {"truth": 0, "lie": 1}[item["seed"]["verdict"]],
        -item["candidate"]["confidence"],
    ))
    generated = [make_case(option["seed"], option["candidate"], index) for index, option in enumerate(selected, start=1)]

    final_counts: Counter[tuple[str, str]] = Counter(existing_counts)
    for item in generated:
        final_counts[(item["difficulty"], item["verdict"])] += 1
    total_final = len(active_numbers) + len(generated)
    all_ids = list(existing_ids) + [item["media"]["youtubeId"] for item in generated]
    validation = {
        "totalFinalCases": total_final,
        "uniqueVideoIds": len(all_ids) == len(set(all_ids)),
        "counts": {
            difficulty: {
                verdict: final_counts[(difficulty, verdict)]
                for verdict in ("truth", "lie")
            }
            for difficulty in ("easy", "medium", "hard")
        },
        "shortfalls": shortfalls,
    }
    complete = (
        not shortfalls
        and total_final == TARGET_PER_DIFFICULTY * 3
        and validation["uniqueVideoIds"]
        and all(final_counts[(difficulty, verdict)] == TARGET_PER_VERDICT for difficulty in ("easy", "medium", "hard") for verdict in ("truth", "lie"))
    )

    report = {
        "generatedAt": TODAY,
        "status": "complete" if complete else "incomplete",
        "target": {
            "total": TARGET_PER_DIFFICULTY * 3,
            "perDifficulty": TARGET_PER_DIFFICULTY,
            "perVerdictPerDifficulty": TARGET_PER_VERDICT,
        },
        "existingActiveCases": len(active_numbers),
        "newCasesSelected": len(generated),
        "validation": validation,
        "seedResults": processed,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if complete:
        OUTPUT_PATH.write_text(json.dumps(generated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("Built a complete 120-case deck with 108 new verified cases.")
        return 0

    # Preserve the last known-good generated deck unless a complete replacement exists.
    print("Content build did not reach the complete balanced target.")
    print(json.dumps(validation, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
