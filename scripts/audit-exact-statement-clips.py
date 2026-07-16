#!/usr/bin/env python3
"""Locate each quoted statement in YouTube captions and build exact clip windows.

The generated window begins 15 seconds before the first matched word and ends
15 seconds after the last matched word, clipped only by the source boundaries.
The script also patches the application so the generated override is applied
last and the YouTube player explicitly seeks to the requested starting point.
"""

from __future__ import annotations

import json
import math
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from rapidfuzz import fuzz
from youtube_transcript_api import YouTubeTranscriptApi

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CASES = DATA / "cases"
WINDOWS_PATH = DATA / "exact-statement-windows.json"
REPORT_PATH = ROOT / "validation" / "exact-statement-audit.json"
MARGIN_SECONDS = 15.0
MIN_ACCEPTED_SCORE = 58.0


@dataclass(frozen=True)
class Caption:
    text: str
    start: float
    duration: float


@dataclass(frozen=True)
class TimedWord:
    token: str
    start: float
    end: float


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def merge_claim(claim: dict[str, Any], override: dict[str, Any] | None) -> dict[str, Any]:
    if not override:
        return claim
    merged = {**claim, **override}
    merged["media"] = {**claim.get("media", {}), **override.get("media", {})}
    return merged


def load_final_claims() -> list[dict[str, Any]]:
    base: list[dict[str, Any]] = []
    for path in sorted(CASES.glob("part??.json")):
        base.extend(read_json(path))

    layers = [
        read_json(DATA / "case-overrides.json"),
        read_json(DATA / "direct-footage-replacements.json"),
        read_json(DATA / "obscure-case-replacements.json"),
        read_json(DATA / "english-weird-replacements.json"),
    ]
    difficulty = read_json(DATA / "difficulty-map.json")

    final: list[dict[str, Any]] = []
    for original in base:
        claim = original
        for layer in layers:
            claim = merge_claim(claim, layer.get(original["caseNumber"]))
        claim = {**claim, "difficulty": difficulty.get(original["caseNumber"], claim.get("difficulty"))}
        final.append(claim)
    return final


def normalize_token(token: str) -> str:
    token = token.lower().replace("’", "'")
    token = re.sub(r"[^a-z0-9']+", "", token)
    replacements = {
        "i'm": "im",
        "i've": "ive",
        "i'd": "id",
        "i'll": "ill",
        "wasn't": "wasnt",
        "weren't": "werent",
        "didn't": "didnt",
        "doesn't": "doesnt",
        "don't": "dont",
        "can't": "cant",
        "couldn't": "couldnt",
        "wouldn't": "wouldnt",
        "they're": "theyre",
        "that's": "thats",
        "there's": "theres",
        "it's": "its",
    }
    return replacements.get(token, token.replace("'", ""))


def tokens(text: str) -> list[str]:
    return [token for raw in text.split() if (token := normalize_token(raw))]


def caption_from_item(item: Any) -> Caption:
    if isinstance(item, dict):
        return Caption(str(item.get("text", "")), float(item.get("start", 0.0)), float(item.get("duration", 0.0)))
    return Caption(str(getattr(item, "text", "")), float(getattr(item, "start", 0.0)), float(getattr(item, "duration", 0.0)))


def fetch_captions(video_id: str) -> list[Caption]:
    api = YouTubeTranscriptApi()
    errors: list[str] = []

    for attempt in range(3):
        try:
            fetched = api.fetch(video_id, languages=["en", "en-US", "en-GB", "en-CA", "en-AU"])
            captions = [caption_from_item(item) for item in fetched]
            if captions:
                return captions
        except Exception as exc:  # noqa: BLE001 - package exception classes vary by release
            errors.append(f"fetch attempt {attempt + 1}: {exc}")
            time.sleep(2**attempt)

    try:
        transcript_list = api.list(video_id)
        candidates = list(transcript_list)
        candidates.sort(key=lambda transcript: (not str(getattr(transcript, "language_code", "")).startswith("en"), bool(getattr(transcript, "is_generated", False))))
        for transcript in candidates:
            try:
                selected = transcript
                if not str(getattr(transcript, "language_code", "")).startswith("en") and bool(getattr(transcript, "is_translatable", False)):
                    selected = transcript.translate("en")
                fetched = selected.fetch()
                captions = [caption_from_item(item) for item in fetched]
                if captions:
                    return captions
            except Exception as exc:  # noqa: BLE001
                errors.append(f"listed transcript: {exc}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"list transcripts: {exc}")

    raise RuntimeError(" | ".join(errors[-5:]) or "No captions returned")


def to_timed_words(captions: Iterable[Caption]) -> list[TimedWord]:
    result: list[TimedWord] = []
    for caption in captions:
        caption_tokens = tokens(caption.text)
        if not caption_tokens:
            continue
        duration = max(0.15, caption.duration)
        step = duration / len(caption_tokens)
        for index, token in enumerate(caption_tokens):
            start = caption.start + index * step
            end = caption.start + (index + 1) * step
            result.append(TimedWord(token, start, end))
    return result


def query_variants(claim: dict[str, Any]) -> list[str]:
    values = [str(claim.get("transcript", "")), str(claim.get("claim", ""))]
    variants: list[str] = []
    for value in values:
        normalized = " ".join(tokens(value))
        if normalized and normalized not in variants:
            variants.append(normalized)
    return variants


def overlap_score(query: list[str], candidate: list[str]) -> float:
    if not query or not candidate:
        return 0.0
    query_set = set(query)
    candidate_set = set(candidate)
    weighted = sum(1 for token in query if token in candidate_set) / len(query)
    rare = [token for token in query if len(token) >= 6]
    rare_overlap = (sum(1 for token in rare if token in candidate_set) / len(rare)) if rare else weighted
    return weighted * 12.0 + rare_overlap * 8.0


def locate_statement(words: list[TimedWord], variants: list[str]) -> tuple[float, float, float, str]:
    if not words or not variants:
        raise RuntimeError("No transcript words or query text")

    best_score = -1.0
    best_start = 0
    best_end = 0
    best_text = ""

    for query_text in variants:
        query_words = query_text.split()
        query_length = len(query_words)
        if query_length == 0:
            continue

        lengths = sorted({
            max(3, int(query_length * 0.55)),
            max(3, int(query_length * 0.75)),
            query_length,
            min(45, max(3, int(query_length * 1.25))),
            min(45, max(3, int(query_length * 1.6))),
        })

        for length in lengths:
            if length > len(words):
                continue
            for start_index in range(0, len(words) - length + 1):
                end_index = start_index + length
                candidate_words = [word.token for word in words[start_index:end_index]]
                candidate_text = " ".join(candidate_words)
                ratio = fuzz.ratio(query_text, candidate_text)
                partial = fuzz.partial_ratio(query_text, candidate_text)
                token_set = fuzz.token_set_ratio(query_text, candidate_text)
                score = max(ratio, partial * 0.97, token_set * 0.94) + overlap_score(query_words, candidate_words)

                span = words[end_index - 1].end - words[start_index].start
                if span > 30:
                    score -= min(12.0, (span - 30) * 0.5)

                if score > best_score:
                    best_score = score
                    best_start = start_index
                    best_end = end_index
                    best_text = candidate_text

    if best_score < 0:
        raise RuntimeError("No candidate window was scored")

    return words[best_start].start, words[best_end - 1].end, min(100.0, best_score), best_text


def round_tenth(value: float) -> float:
    return round(value + 1e-9, 1)


def exact_window(statement_start: float, statement_end: float, duration: float) -> tuple[float, float]:
    start = max(0.0, statement_start - MARGIN_SECONDS)
    end = min(duration, statement_end + MARGIN_SECONDS)
    return round_tenth(start), round_tenth(end)


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"Expected patch anchor not found in {path}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_application() -> None:
    claims = ROOT / "lib" / "claims.ts"
    replace_once(
        claims,
        'import rawEnglishWeirdReplacements from "@/data/english-weird-replacements.json";\n',
        'import rawEnglishWeirdReplacements from "@/data/english-weird-replacements.json";\nimport rawExactStatementWindows from "@/data/exact-statement-windows.json";\n',
    )
    replace_once(
        claims,
        "const englishWeirdReplacements = rawEnglishWeirdReplacements as Record<string, ClaimOverride>;\n",
        "const englishWeirdReplacements = rawEnglishWeirdReplacements as Record<string, ClaimOverride>;\nconst exactStatementWindows = rawExactStatementWindows as Record<string, ClaimOverride>;\n",
    )
    replace_once(
        claims,
        "  const english = applyOverride(obscure, englishWeirdReplacements[claim.caseNumber]);\n  return {\n    ...english,\n    difficulty: difficultyMap[claim.caseNumber] ?? english.difficulty,\n",
        "  const english = applyOverride(obscure, englishWeirdReplacements[claim.caseNumber]);\n  const exact = applyOverride(english, exactStatementWindows[claim.caseNumber]);\n  return {\n    ...exact,\n    difficulty: difficultyMap[claim.caseNumber] ?? exact.difficulty,\n",
    )

    types = ROOT / "lib" / "types.ts"
    replace_once(
        types,
        "  endSeconds: number;\n  videoDurationSeconds: number;\n",
        "  endSeconds: number;\n  statementStartSeconds: number;\n  statementEndSeconds: number;\n  transcriptMatchScore: number;\n  transcriptMatchText: string;\n  videoDurationSeconds: number;\n",
    )

    validator = ROOT / "scripts" / "validate-detective-cases.mjs"
    replace_once(
        validator,
        'const englishWeirdReplacements = JSON.parse(readFileSync(resolve("data/english-weird-replacements.json"), "utf8"));\n',
        'const englishWeirdReplacements = JSON.parse(readFileSync(resolve("data/english-weird-replacements.json"), "utf8"));\nconst exactStatementWindows = JSON.parse(readFileSync(resolve("data/exact-statement-windows.json"), "utf8"));\n',
    )
    replace_once(
        validator,
        "  const english = applyOverride(obscure, englishWeirdReplacements[claim.caseNumber]);\n  return { ...english, difficulty: difficultyMap[claim.caseNumber] ?? english.difficulty };\n",
        "  const english = applyOverride(obscure, englishWeirdReplacements[claim.caseNumber]);\n  const exact = applyOverride(english, exactStatementWindows[claim.caseNumber]);\n  return { ...exact, difficulty: difficultyMap[claim.caseNumber] ?? exact.difficulty };\n",
    )
    replace_once(
        validator,
        "if (Object.keys(englishWeirdReplacements).length !== 2) failures.push(`Expected 2 English weird-truth replacements, found ${Object.keys(englishWeirdReplacements).length}.`);\n",
        "if (Object.keys(englishWeirdReplacements).length !== 2) failures.push(`Expected 2 English weird-truth replacements, found ${Object.keys(englishWeirdReplacements).length}.`);\nif (Object.keys(exactStatementWindows).length !== 50) failures.push(`Expected 50 exact statement windows, found ${Object.keys(exactStatementWindows).length}.`);\n",
    )
    replace_once(
        validator,
        "  const duration = media.videoDurationSeconds;\n  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end <= start) failures.push(`${label}: invalid clip window ${start}-${end}.`);\n  else if (end - start > 45) failures.push(`${label}: clip is ${end - start}s; maximum is 45s.`);\n  if (!Number.isInteger(duration) || duration < end) failures.push(`${label}: source duration ${duration} does not cover clip end ${end}.`);\n",
        "  const duration = media.videoDurationSeconds;\n  const statementStart = media.statementStartSeconds;\n  const statementEnd = media.statementEndSeconds;\n  const finite = (value) => typeof value === \"number\" && Number.isFinite(value);\n  if (![start, end, statementStart, statementEnd, duration].every(finite) || start < 0 || end <= start || statementEnd <= statementStart) failures.push(`${label}: invalid clip or statement window.`);\n  else {\n    const expectedStart = Math.max(0, statementStart - 15);\n    const expectedEnd = Math.min(duration, statementEnd + 15);\n    if (Math.abs(start - expectedStart) > 0.11) failures.push(`${label}: clip must start exactly 15 seconds before the statement (or at 0).`);\n    if (Math.abs(end - expectedEnd) > 0.11) failures.push(`${label}: clip must end exactly 15 seconds after the statement (or at source end).`);\n    if (end - start > 60) failures.push(`${label}: transcript match spans too long (${end - start}s).`);\n  }\n  if (!Number.isInteger(duration) || duration < end) failures.push(`${label}: source duration ${duration} does not cover clip end ${end}.`);\n  if (!finite(media.transcriptMatchScore) || media.transcriptMatchScore < 58) failures.push(`${label}: transcript match confidence is too low.`);\n",
    )
    replace_once(
        validator,
        "console.log(`Validated 50 cases: 25 truth, 25 lie; balanced Easy/Hard/Expert decks; every clip <=45 seconds.`);\n",
        "console.log(`Validated 50 cases: every playable excerpt starts 15 seconds before its matched statement and ends 15 seconds after it.`);\n",
    )

    player = ROOT / "components" / "ClipPlayer.tsx"
    replace_once(
        player,
        "  getCurrentTime(): number;\n  destroy(): void;\n",
        "  getCurrentTime(): number;\n  seekTo(seconds: number, allowSeekAhead: boolean): void;\n  destroy(): void;\n",
    )
    replace_once(
        player,
        "  return [...(SOURCE_REPLACEMENTS[videoId] ?? []), primary];\n",
        "  return [primary, ...(SOURCE_REPLACEMENTS[videoId] ?? [])];\n",
    )
    replace_once(
        player,
        "            cc_load_policy: 1,\n            origin: window.location.origin,\n",
        "            cc_load_policy: 1,\n            start: activeSource.startSeconds,\n            end: activeSource.endSeconds,\n            origin: window.location.origin,\n",
    )
    replace_once(
        player,
        "              target.cueVideoById({\n                videoId: activeSource.videoId,\n                startSeconds: activeSource.startSeconds,\n                endSeconds: activeSource.endSeconds,\n              });\n              setReady(true);\n",
        "              target.cueVideoById({\n                videoId: activeSource.videoId,\n                startSeconds: activeSource.startSeconds,\n                endSeconds: activeSource.endSeconds,\n              });\n              target.seekTo(activeSource.startSeconds, true);\n              target.pauseVideo();\n              setReady(true);\n",
    )
    replace_once(
        player,
        "              setPlaying(data === YT.PlayerState.PLAYING);\n              if (data === YT.PlayerState.ENDED) {\n",
        "              setPlaying(data === YT.PlayerState.PLAYING);\n              if (data === YT.PlayerState.CUED) {\n                target.seekTo(activeSource.startSeconds, true);\n              }\n              if (data === YT.PlayerState.PLAYING) {\n                const current = target.getCurrentTime();\n                if (current < activeSource.startSeconds - 0.5 || current >= activeSource.endSeconds) {\n                  target.seekTo(activeSource.startSeconds, true);\n                }\n              }\n              if (data === YT.PlayerState.ENDED) {\n",
    )
    replace_once(
        player,
        "      player.loadVideoById({\n        videoId: activeSource.videoId,\n        startSeconds: activeSource.startSeconds,\n        endSeconds: activeSource.endSeconds,\n      });\n      return;\n",
        "      player.loadVideoById({\n        videoId: activeSource.videoId,\n        startSeconds: activeSource.startSeconds,\n        endSeconds: activeSource.endSeconds,\n      });\n      window.setTimeout(() => player.seekTo(activeSource.startSeconds, true), 0);\n      return;\n",
    )
    replace_once(
        player,
        "    player.loadVideoById({\n      videoId: activeSource.videoId,\n      startSeconds: activeSource.startSeconds,\n      endSeconds: activeSource.endSeconds,\n    });\n  }\n",
        "    player.loadVideoById({\n      videoId: activeSource.videoId,\n      startSeconds: activeSource.startSeconds,\n      endSeconds: activeSource.endSeconds,\n    });\n    window.setTimeout(() => player.seekTo(activeSource.startSeconds, true), 0);\n  }\n",
    )

    home = ROOT / "app" / "page.tsx"
    replace_once(
        home,
        "        <span><strong>≤45s</strong><small>per clip</small></span>\n",
        "        <span><strong>±15s</strong><small>around each statement</small></span>\n",
    )


def main() -> int:
    claims = load_final_claims()
    if len(claims) != 50:
        raise RuntimeError(f"Expected 50 claims, found {len(claims)}")

    overrides: dict[str, Any] = {}
    report: dict[str, Any] = {"marginSeconds": MARGIN_SECONDS, "cases": [], "failures": []}

    for index, claim in enumerate(claims, start=1):
        case_number = claim["caseNumber"]
        media = claim["media"]
        video_id = media["youtubeId"]
        duration = float(media["videoDurationSeconds"])
        print(f"[{index:02d}/50] {case_number} {claim['person']} ({video_id})", flush=True)
        try:
            captions = fetch_captions(video_id)
            timed_words = to_timed_words(captions)
            statement_start, statement_end, score, match_text = locate_statement(timed_words, query_variants(claim))
            if score < MIN_ACCEPTED_SCORE:
                raise RuntimeError(f"Best transcript match scored {score:.1f}, below {MIN_ACCEPTED_SCORE:.1f}")

            statement_start = round_tenth(statement_start)
            statement_end = round_tenth(statement_end)
            start, end = exact_window(statement_start, statement_end, duration)
            if end <= start:
                raise RuntimeError(f"Invalid generated range {start}-{end}")

            overrides[case_number] = {
                "media": {
                    "startSeconds": start,
                    "endSeconds": end,
                    "statementStartSeconds": statement_start,
                    "statementEndSeconds": statement_end,
                    "transcriptMatchScore": round_tenth(score),
                    "transcriptMatchText": match_text,
                    "url": f"https://www.youtube.com/watch?v={video_id}&t={start:g}s",
                    "verifiedAt": "2026-07-16",
                }
            }
            report["cases"].append({
                "caseNumber": case_number,
                "person": claim["person"],
                "videoId": video_id,
                "query": query_variants(claim),
                "matchedText": match_text,
                "score": round_tenth(score),
                "statementStartSeconds": statement_start,
                "statementEndSeconds": statement_end,
                "startSeconds": start,
                "endSeconds": end,
            })
        except Exception as exc:  # noqa: BLE001
            message = str(exc)
            print(f"  FAILED: {message}", file=sys.stderr, flush=True)
            report["failures"].append({"caseNumber": case_number, "person": claim["person"], "videoId": video_id, "error": message})
        time.sleep(0.8)

    write_json(REPORT_PATH, report)
    if report["failures"]:
        print(f"Timestamp audit failed for {len(report['failures'])} case(s). See {REPORT_PATH}.", file=sys.stderr)
        return 1

    write_json(WINDOWS_PATH, overrides)
    patch_application()
    print(f"Wrote {len(overrides)} exact statement windows to {WINDOWS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
