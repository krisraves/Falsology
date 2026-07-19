#!/usr/bin/env python3
"""Verify Falsology's 300-video editorial candidate pool.

A candidate is marked VERIFIED only when all automated gates pass:
- unique YouTube ID
- public, available, non-live, embeddable video
- usable English timed transcript
- high-confidence exact statement match to the research query
- direct-footage indicators (subject/title/transcript, no reaction package)
- a provisional truth/lie classification supported by a secondary reference

The automated verdict gate is deliberately conservative. Anything ambiguous is
left in NEEDS_EDITORIAL_REVIEW and is never activated automatically.
"""

from __future__ import annotations

import concurrent.futures
import difflib
import html
import json
import math
import re
import subprocess
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "research" / "video-candidates.json"
REPORT = ROOT / "data" / "research" / "video-verification-report.json"
VERIFIED = ROOT / "data" / "research" / "verified-video-candidates.json"
SUMMARY = ROOT / "data" / "research" / "video-verification-summary.md"

METADATA_WORKERS = 8
VERIFY_WORKERS = 5
HTTP_TIMEOUT = 35
TRANSCRIPT_ENDPOINT = "https://youtube2text.diguardia.org/api/transcript"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"

GENERIC_QUERY_WORDS = {
    "full", "video", "footage", "direct", "archive", "archival", "historical", "original", "raw",
    "interview", "interrogation", "testimony", "hearing", "statement", "speech", "confession",
    "deposition", "press", "conference", "court", "courtroom", "trial", "documentary", "episode",
    "clip", "police", "parole", "congressional", "primary", "sources", "source", "translated",
    "testifies", "testify", "inquiry", "inquest", "recording", "tape", "tapes", "survivor",
}

MATCH_STOP_WORDS = GENERIC_QUERY_WORDS | {
    "the", "and", "that", "this", "with", "from", "into", "about", "after", "before", "during",
    "where", "when", "what", "which", "would", "could", "should", "have", "has", "had", "was",
    "were", "are", "been", "being", "not", "for", "but", "you", "your", "they", "their", "them",
    "his", "her", "its", "our", "who", "why", "how", "did", "does", "doing", "over", "under",
    "case", "event", "claims", "claim", "denial", "admission", "fraud", "scandal", "false", "true",
}

FIRST_PERSON = re.compile(r"\b(i|i'm|im|i've|ive|i'd|id|i'll|ill|me|my|mine|we|we're|were|we've|our|ours)\b", re.I)
QUESTION = re.compile(r"\b(did you|do you|are you|were you|can you|could you|would you|tell me|what did|why did|how did)\b", re.I)
REJECT_TITLE = re.compile(r"\b(reaction|reacts|analysis|explained|body language|compilation|top 10|shorts|podcast reacts|breakdown)\b", re.I)
DIRECT_TITLE = re.compile(r"\b(interview|interrogation|testimony|hearing|statement|speech|confession|deposition|press conference|court|trial|full|raw)\b", re.I)

LIE_QUERY_TERMS = {
    "denial", "false", "hoax", "fraud", "misleading", "not a crook", "not addictive", "sniper fire",
    "false alibi", "fake", "lied", "lie", "fabricated", "staged", "scam", "deception",
}
TRUTH_QUERY_TERMS = {
    "confession", "confessed", "admission", "admitted", "exoneration", "exonerated", "survivor",
    "survived", "dna", "innocent", "release statement", "i killed", "i bit", "i was involved",
    "rescued", "escaped", "truth commission", "guilty plea",
}
LIE_EVIDENCE_TERMS = {
    "false", "falsely", "fraud", "fraudulent", "hoax", "fabricated", "misled", "misleading", "lied",
    "admitted", "confessed", "convicted", "guilty", "pleaded guilty", "disproved", "retracted",
    "indicted", "charged", "deception", "forged", "forgery",
}
TRUTH_EVIDENCE_TERMS = {
    "survived", "rescued", "escaped", "exonerated", "innocent", "dna", "confessed", "admitted",
    "convicted", "guilty", "confirmed", "verified", "released", "acquitted", "overturned",
}


@dataclass
class Segment:
    start: float
    end: float
    text: str


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clean_text(value: str) -> str:
    return " ".join(html.unescape(value or "").replace("\u200b", " ").split())


def words(value: str, *, stop: set[str] | None = None) -> list[str]:
    stop = stop or set()
    return [token for token in re.sub(r"[^a-z0-9']+", " ", value.lower()).split() if len(token) > 1 and token not in stop]


def ratio(left: str, right: str) -> float:
    return difflib.SequenceMatcher(None, left.lower(), right.lower()).ratio()


def likely_subject(query: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9.'-]+", query)
    subject: list[str] = []
    for token in tokens:
        lowered = token.lower().strip(".'-")
        if lowered in GENERIC_QUERY_WORDS or lowered in {"i", "we", "my", "our", "a", "an", "the"}:
            break
        if token[:1].isupper() or token.isupper() or len(subject) < 2:
            subject.append(token)
        else:
            break
        if len(subject) >= 5:
            break
    return " ".join(subject).strip()


def statement_hint(query: str, subject: str) -> str:
    value = query
    if subject and value.lower().startswith(subject.lower()):
        value = value[len(subject):]
    tokens = re.findall(r"[A-Za-z0-9']+", value)
    filtered = [token for token in tokens if token.lower() not in GENERIC_QUERY_WORDS]
    result = " ".join(filtered).strip()
    if len(words(result, stop=MATCH_STOP_WORDS)) < 2:
        return ""
    return result


def run_metadata(video_id: str) -> dict[str, Any]:
    url = f"https://www.youtube.com/watch?v={video_id}"
    command = [
        "yt-dlp", "--dump-single-json", "--skip-download", "--no-warnings", "--no-playlist",
        "--socket-timeout", "25", "--retries", "2", url,
    ]
    try:
        process = subprocess.run(command, capture_output=True, text=True, timeout=80, check=False)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "metadata timeout"}
    if process.returncode != 0:
        error = clean_text(process.stderr)[-600:] or f"yt-dlp exit {process.returncode}"
        return {"ok": False, "error": error}
    try:
        info = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"invalid metadata JSON: {exc}"}
    return {"ok": True, "info": info}


def parse_json3(payload: dict[str, Any]) -> list[Segment]:
    result: list[Segment] = []
    for event in payload.get("events", []):
        segs = event.get("segs") or []
        text = clean_text("".join(str(seg.get("utf8", "")) for seg in segs))
        if not text:
            continue
        start = float(event.get("tStartMs", 0)) / 1000
        duration = float(event.get("dDurationMs", 0)) / 1000
        if duration <= 0:
            duration = 2.5
        result.append(Segment(start=start, end=start + duration, text=text))
    return result


def parse_vtt(content: str) -> list[Segment]:
    result: list[Segment] = []
    current_start: float | None = None
    current_end: float | None = None
    lines: list[str] = []

    def timestamp(value: str) -> float:
        pieces = value.replace(",", ".").split(":")
        if len(pieces) == 2:
            minutes, seconds = pieces
            return float(minutes) * 60 + float(seconds)
        hours, minutes, seconds = pieces
        return float(hours) * 3600 + float(minutes) * 60 + float(seconds)

    def flush() -> None:
        nonlocal current_start, current_end, lines
        text = clean_text(" ".join(re.sub(r"<[^>]+>", "", line) for line in lines))
        if current_start is not None and current_end is not None and text:
            if not result or text != result[-1].text:
                result.append(Segment(current_start, current_end, text))
        current_start = current_end = None
        lines = []

    for raw in content.splitlines():
        line = raw.strip()
        if "-->" in line:
            flush()
            left, right = [part.strip().split()[0] for part in line.split("-->", 1)]
            try:
                current_start, current_end = timestamp(left), timestamp(right)
            except Exception:
                current_start = current_end = None
        elif not line:
            flush()
        elif current_start is not None and not line.isdigit() and not line.startswith(("WEBVTT", "Kind:", "Language:")):
            lines.append(line)
    flush()
    return result


def subtitle_tracks(info: dict[str, Any]) -> list[dict[str, Any]]:
    tracks: list[dict[str, Any]] = []
    for source_name in ("subtitles", "automatic_captions"):
        source = info.get(source_name) or {}
        keys = [key for key in source if key.lower() == "en"] + [key for key in source if key.lower().startswith("en-")]
        for key in keys:
            for track in source.get(key) or []:
                if track.get("url"):
                    tracks.append({**track, "language": key, "source": source_name})
    tracks.sort(key=lambda item: (item.get("source") != "subtitles", item.get("ext") not in {"json3", "vtt"}))
    return tracks


def fetch_transcript(info: dict[str, Any], video_id: str, session: requests.Session) -> tuple[list[Segment], str, str | None]:
    headers = {"User-Agent": USER_AGENT}
    errors: list[str] = []
    for track in subtitle_tracks(info):
        try:
            response = session.get(track["url"], headers=headers, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            ext = str(track.get("ext", ""))
            if ext == "json3" or response.text.lstrip().startswith("{"):
                segments = parse_json3(response.json())
            else:
                segments = parse_vtt(response.text)
            if segments:
                return segments, f"youtube-{track.get('source')}-{track.get('language')}-{ext}", None
        except Exception as exc:  # noqa: BLE001
            errors.append(f"subtitle {track.get('ext')}: {type(exc).__name__}")

    try:
        response = session.post(
            TRANSCRIPT_ENDPOINT,
            json={"url": f"https://www.youtube.com/watch?v={video_id}", "lang": "en"},
            headers={"User-Agent": USER_AGENT, "Origin": "https://youtube2text.diguardia.org", "Referer": "https://youtube2text.diguardia.org/"},
            timeout=55,
        )
        response.raise_for_status()
        payload = response.json()
        segments = []
        for item in payload.get("segments") or []:
            text = clean_text(str(item.get("text", "")))
            start = float(item.get("start", 0))
            duration = float(item.get("duration", 0))
            if text and duration > 0:
                segments.append(Segment(start, start + duration, text))
        if segments:
            return segments, "youtube2text", None
    except Exception as exc:  # noqa: BLE001
        errors.append(f"fallback: {type(exc).__name__}: {exc}")
    return [], "none", " | ".join(errors)[-1000:] or "no English timed transcript"


def best_statement(segments: list[Segment], hint: str) -> dict[str, Any] | None:
    target_tokens = words(hint, stop=MATCH_STOP_WORDS)
    if len(set(target_tokens)) < 2:
        return None
    target = " ".join(target_tokens)
    target_counter = Counter(target_tokens)
    candidates: list[dict[str, Any]] = []
    for start_index in range(len(segments)):
        combined: list[str] = []
        for end_index in range(start_index, min(len(segments), start_index + 6)):
            combined.append(segments[end_index].text)
            text = clean_text(" ".join(combined))
            text_tokens = words(text, stop=MATCH_STOP_WORDS)
            if not text_tokens or len(text_tokens) > 70:
                continue
            text_counter = Counter(text_tokens)
            overlap = sum((target_counter & text_counter).values())
            coverage = overlap / max(1, sum(target_counter.values()))
            precision = overlap / max(1, sum(text_counter.values()))
            fuzzy = ratio(target, " ".join(text_tokens))
            score = coverage * 60 + fuzzy * 25 + min(precision, 0.8) * 10
            if FIRST_PERSON.search(text):
                score += 8
            if QUESTION.search(text):
                score -= 8
            candidates.append({
                "score": round(score, 2),
                "coverage": round(coverage, 3),
                "precision": round(precision, 3),
                "fuzzy": round(fuzzy, 3),
                "startSeconds": round(segments[start_index].start, 2),
                "endSeconds": round(segments[end_index].end, 2),
                "text": text,
                "firstPerson": bool(FIRST_PERSON.search(text)),
            })
    if not candidates:
        return None
    candidates.sort(key=lambda item: item["score"], reverse=True)
    return candidates[0]


def wikipedia_reference(query: str, session: requests.Session) -> dict[str, Any] | None:
    api = "https://en.wikipedia.org/w/api.php"
    headers = {"User-Agent": "FalsologyEditorialVerifier/1.0 (research; contact via GitHub)"}
    search_terms = " ".join(token for token in re.findall(r"[A-Za-z0-9'-]+", query) if token.lower() not in GENERIC_QUERY_WORDS)
    if not search_terms:
        return None
    try:
        search_response = session.get(api, params={"action": "query", "list": "search", "srsearch": search_terms, "srlimit": 3, "format": "json", "utf8": 1}, headers=headers, timeout=HTTP_TIMEOUT)
        search_response.raise_for_status()
        results = search_response.json().get("query", {}).get("search", [])
        if not results:
            return None
        best = results[0]
        title = best["title"]
        page_response = session.get(api, params={"action": "query", "prop": "extracts|info", "exintro": 1, "explaintext": 1, "inprop": "url", "titles": title, "format": "json", "utf8": 1}, headers=headers, timeout=HTTP_TIMEOUT)
        page_response.raise_for_status()
        pages = page_response.json().get("query", {}).get("pages", {})
        page = next(iter(pages.values()))
        extract = clean_text(page.get("extract", ""))
        return {"title": title, "url": page.get("fullurl") or f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}", "extract": extract[:3500], "searchSnippet": clean_text(re.sub(r"<[^>]+>", "", best.get("snippet", "")))}
    except Exception:
        return None


def verdict_hypothesis(query: str) -> str | None:
    lowered = query.lower()
    lie_score = sum(1 for term in LIE_QUERY_TERMS if term in lowered)
    truth_score = sum(1 for term in TRUTH_QUERY_TERMS if term in lowered)
    if lie_score > truth_score and lie_score:
        return "lie"
    if truth_score > lie_score and truth_score:
        return "truth"
    return None


def evidence_support(verdict: str | None, reference: dict[str, Any] | None) -> dict[str, Any]:
    if not verdict or not reference:
        return {"supported": False, "hits": []}
    text = f"{reference.get('title', '')} {reference.get('extract', '')}".lower()
    terms = LIE_EVIDENCE_TERMS if verdict == "lie" else TRUTH_EVIDENCE_TERMS
    hits = sorted(term for term in terms if term in text)
    return {"supported": len(hits) >= 1, "hits": hits[:12]}


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def verify_candidate(candidate: dict[str, Any], duplicate_ids: set[str]) -> dict[str, Any]:
    video_id = candidate["videoId"]
    result: dict[str, Any] = {
        **candidate,
        "verificationStatus": "needs_editorial_review",
        "verifiedAt": now_iso(),
        "checks": {},
        "issues": [],
    }

    result["checks"]["uniqueVideoId"] = video_id not in duplicate_ids
    if video_id in duplicate_ids:
        result["issues"].append("Duplicate YouTube ID in candidate pool")

    metadata = run_metadata(video_id)
    if not metadata.get("ok"):
        result["checks"]["videoAvailable"] = False
        result["issues"].append(f"Video unavailable: {metadata.get('error')}")
        result["verificationStatus"] = "rejected"
        return result

    info = metadata["info"]
    duration = info.get("duration")
    availability = str(info.get("availability") or "public")
    live_status = str(info.get("live_status") or "not_live")
    playable_in_embed = info.get("playable_in_embed")
    title = clean_text(str(info.get("title") or candidate.get("title") or ""))
    channel = clean_text(str(info.get("channel") or info.get("uploader") or candidate.get("channel") or ""))
    description = clean_text(str(info.get("description") or ""))
    public = availability in {"public", "unlisted"}
    non_live = not bool(info.get("is_live")) and live_status not in {"is_live", "is_upcoming", "post_live"}
    embed_ok = playable_in_embed is not False
    valid_duration = finite_number(duration) and float(duration) > 2

    result["metadata"] = {
        "title": title,
        "channel": channel,
        "durationSeconds": duration,
        "availability": availability,
        "liveStatus": live_status,
        "playableInEmbed": playable_in_embed,
        "ageLimit": info.get("age_limit"),
        "webpageUrl": info.get("webpage_url") or candidate.get("url"),
    }
    result["checks"].update({"videoAvailable": public and valid_duration, "nonLive": non_live, "embeddable": embed_ok})
    if not public or not valid_duration:
        result["issues"].append("Video is not a usable public recording")
    if not non_live:
        result["issues"].append("Video is live or upcoming")
    if not embed_ok:
        result["issues"].append("Uploader has disabled embedding")

    session = requests.Session()
    segments, transcript_source, transcript_error = fetch_transcript(info, video_id, session)
    result["transcript"] = {"available": bool(segments), "source": transcript_source, "segmentCount": len(segments), "error": transcript_error}
    result["checks"]["timedEnglishTranscript"] = bool(segments)
    if not segments:
        result["issues"].append("No usable English timed transcript")

    query = str(candidate.get("searchQuery") or "")
    subject = likely_subject(query)
    hint = statement_hint(query, subject)
    match = best_statement(segments, hint) if segments and hint else None
    if match:
        statement_confidence = min(1.0, max(0.0, match["score"] / 100))
        clip_start = max(0.0, match["startSeconds"] - 15)
        clip_end = min(float(duration), match["endSeconds"] + 15) if valid_duration else match["endSeconds"] + 15
        result["exactStatement"] = {**match, "hint": hint, "confidence": round(statement_confidence, 3), "clipStartSeconds": round(clip_start, 2), "clipEndSeconds": round(clip_end, 2)}
    else:
        statement_confidence = 0.0
        result["exactStatement"] = None
    exact_ok = bool(match and match["coverage"] >= 0.62 and match["fuzzy"] >= 0.52 and match["firstPerson"] and match["score"] >= 62)
    result["checks"]["exactStatementMatched"] = exact_ok
    if not exact_ok:
        result["issues"].append("Research query does not identify a high-confidence exact first-person statement in this transcript")

    subject_tokens = set(words(subject))
    title_tokens = set(words(title))
    subject_overlap = len(subject_tokens & title_tokens) / max(1, len(subject_tokens)) if subject_tokens else 0.0
    direct_score = 0.0
    direct_score += 0.35 if subject_overlap >= 0.6 else subject_overlap * 0.35
    direct_score += 0.25 if DIRECT_TITLE.search(title) else 0.0
    direct_score += 0.30 if match and match.get("firstPerson") else 0.0
    direct_score += 0.10 if candidate.get("directFootageLikely") else 0.0
    if REJECT_TITLE.search(title):
        direct_score -= 0.55
    if "documentary" in title.lower() and not DIRECT_TITLE.search(title.replace("documentary", "")):
        direct_score -= 0.20
    direct_score = max(0.0, min(1.0, direct_score))
    direct_ok = direct_score >= 0.70 and not REJECT_TITLE.search(title)
    result["directFootage"] = {"subject": subject, "subjectTitleOverlap": round(subject_overlap, 3), "confidence": round(direct_score, 3), "titleHasDirectIndicator": bool(DIRECT_TITLE.search(title)), "titleHasRejectedFormat": bool(REJECT_TITLE.search(title))}
    result["checks"]["directFootage"] = direct_ok
    if not direct_ok:
        result["issues"].append("Direct-footage confidence is below the publishing threshold")

    reference = wikipedia_reference(query, session)
    verdict = verdict_hypothesis(query)
    support = evidence_support(verdict, reference)
    result["verdictReview"] = {"hypothesis": verdict, "secondaryReference": reference, "support": support, "primarySource": info.get("webpage_url") or candidate.get("url")}
    evidence_ok = bool(verdict and reference and support["supported"])
    result["checks"]["evidenceBackedVerdict"] = evidence_ok
    if not evidence_ok:
        result["issues"].append("Truth/lie verdict is not sufficiently supported by the automated secondary-reference check")

    required = ["uniqueVideoId", "videoAvailable", "nonLive", "embeddable", "timedEnglishTranscript", "exactStatementMatched", "directFootage", "evidenceBackedVerdict"]
    passed = all(result["checks"].get(key) is True for key in required)
    if passed:
        result["verificationStatus"] = "verified"
        result["issues"] = []
    elif not result["checks"].get("videoAvailable") or not result["checks"].get("embeddable") or bool(REJECT_TITLE.search(title)):
        result["verificationStatus"] = "rejected"
    return result


def markdown_summary(report: dict[str, Any]) -> str:
    lines = [
        "# Falsology 300-Video Verification",
        "",
        f"Generated: {report['generatedAt']}",
        "",
        "A video is listed as **verified** only when it passes availability, embedding, transcript, exact-statement, direct-footage, uniqueness, and evidence-backed-verdict gates.",
        "",
        "## Totals",
        "",
        f"- Verified: **{report['summary']['verified']}**",
        f"- Needs editorial review: **{report['summary']['needs_editorial_review']}**",
        f"- Rejected: **{report['summary']['rejected']}**",
        "",
        "## By difficulty",
        "",
        "| Difficulty | Verified | Needs review | Rejected |",
        "|---|---:|---:|---:|",
    ]
    for difficulty in ("easy", "hard", "expert"):
        row = report["byDifficulty"][difficulty]
        lines.append(f"| {difficulty.title()} | {row.get('verified', 0)} | {row.get('needs_editorial_review', 0)} | {row.get('rejected', 0)} |")
    lines.extend(["", "## Gate failures", ""])
    for issue, count in report["issueCounts"][:20]:
        lines.append(f"- {count}: {issue}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    raw = json.loads(INPUT.read_text(encoding="utf-8"))
    candidates: list[dict[str, Any]] = []
    for difficulty in ("easy", "hard", "expert"):
        for item in raw.get("candidates", {}).get(difficulty, []):
            candidates.append({**item, "difficulty": difficulty})

    ids = [item["videoId"] for item in candidates]
    counts = Counter(ids)
    duplicate_ids = {video_id for video_id, count in counts.items() if count > 1}

    results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=VERIFY_WORKERS) as executor:
        futures = {executor.submit(verify_candidate, candidate, duplicate_ids): candidate for candidate in candidates}
        for completed, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            candidate = futures[future]
            try:
                result = future.result()
            except Exception as exc:  # noqa: BLE001
                result = {**candidate, "verificationStatus": "needs_editorial_review", "verifiedAt": now_iso(), "checks": {}, "issues": [f"Verifier exception: {type(exc).__name__}: {exc}"]}
            results.append(result)
            print(f"[{completed}/{len(candidates)}] {candidate['difficulty']} {candidate['videoId']}: {result['verificationStatus']}", flush=True)

    order = {item["videoId"]: index for index, item in enumerate(candidates)}
    results.sort(key=lambda item: order[item["videoId"]])
    summary = Counter(item["verificationStatus"] for item in results)
    by_difficulty: dict[str, Counter[str]] = defaultdict(Counter)
    issue_counts: Counter[str] = Counter()
    for item in results:
        by_difficulty[item["difficulty"]][item["verificationStatus"]] += 1
        issue_counts.update(item.get("issues") or [])

    report = {
        "generatedAt": now_iso(),
        "methodVersion": 1,
        "criteria": [
            "Unique YouTube ID",
            "Public, available, non-live recording",
            "Embedding permitted",
            "English timed transcript available",
            "High-confidence exact first-person statement match",
            "Direct-footage indicators and no reaction/analysis packaging",
            "Provisional verdict supported by the source video and a secondary reference",
        ],
        "candidateCount": len(results),
        "summary": {key: summary.get(key, 0) for key in ("verified", "needs_editorial_review", "rejected")},
        "byDifficulty": {difficulty: {key: by_difficulty[difficulty].get(key, 0) for key in ("verified", "needs_editorial_review", "rejected")} for difficulty in ("easy", "hard", "expert")},
        "issueCounts": issue_counts.most_common(),
        "results": results,
    }
    verified = {
        "generatedAt": report["generatedAt"],
        "notice": "Only candidates passing every automated verification gate are included. Editorial review remains recommended before publication.",
        "count": summary.get("verified", 0),
        "candidates": {difficulty: [item for item in results if item["difficulty"] == difficulty and item["verificationStatus"] == "verified"] for difficulty in ("easy", "hard", "expert")},
    }

    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    VERIFIED.write_text(json.dumps(verified, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    SUMMARY.write_text(markdown_summary(report) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
