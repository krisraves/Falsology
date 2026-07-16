#!/usr/bin/env python3
"""Run the exact-statement audit with caption mirror fallbacks.

YouTube rejects most caption requests from cloud-hosted CI runners. This wrapper
loads the audit module and replaces its caption fetcher with independent
Invidious and Piped endpoints. The matcher and all validation remain unchanged.
"""

from __future__ import annotations

import html
import importlib.util
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "scripts" / "audit-exact-statement-clips.py"
USER_AGENT = "Mozilla/5.0 (compatible; FalsologyTimestampAudit/1.0)"
TIMEOUT_SECONDS = 25

INVIDIOUS_INSTANCES = (
    "https://inv.nadeko.net",
    "https://invidious.nerdvpn.de",
    "https://yt.chocolatemoo53.com",
    "https://invidious.tiekoetter.com",
    "https://invidious.f5.si",
    "https://inv.zoomerville.com",
)

PIPED_INSTANCES = (
    "https://pipedapi.adminforge.de",
    "https://pipedapi.reallyaweso.me",
    "https://pipedapi.kavin.rocks",
    "https://pipedapi-libre.kavin.rocks",
)

TIMESTAMP_RE = re.compile(
    r"(?:(?P<sh>\d{1,2}):)?(?P<sm>\d{2}):(?P<ss>\d{2}(?:[.,]\d+)?)\s+-->\s+"
    r"(?:(?P<eh>\d{1,2}):)?(?P<em>\d{2}):(?P<es>\d{2}(?:[.,]\d+)?)"
)
TAG_RE = re.compile(r"<[^>]+>")


def load_audit_module() -> Any:
    spec = importlib.util.spec_from_file_location("falsology_exact_statement_audit", AUDIT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {AUDIT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def request_bytes(url: str, accept: str = "*/*") -> tuple[bytes, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": accept,
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        content_type = response.headers.get("Content-Type", "")
        return response.read(), content_type


def timestamp_seconds(hours: str | None, minutes: str, seconds: str) -> float:
    return int(hours or 0) * 3600 + int(minutes) * 60 + float(seconds.replace(",", "."))


def clean_caption_text(lines: list[str]) -> str:
    text = " ".join(line.strip() for line in lines if line.strip())
    text = TAG_RE.sub("", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_webvtt(payload: bytes, caption_class: type[Any]) -> list[Any]:
    text = payload.decode("utf-8-sig", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    if "WEBVTT" not in text[:100].upper() and "-->" not in text:
        raise ValueError("Response is not WebVTT")

    captions: list[Any] = []
    blocks = re.split(r"\n\s*\n", text)
    for block in blocks:
        lines = [line for line in block.split("\n") if line.strip()]
        if not lines or lines[0].lstrip().startswith(("WEBVTT", "NOTE", "STYLE", "REGION")):
            continue

        timing_index = next((index for index, line in enumerate(lines) if "-->" in line), None)
        if timing_index is None:
            continue
        match = TIMESTAMP_RE.search(lines[timing_index])
        if not match:
            continue

        start = timestamp_seconds(match.group("sh"), match.group("sm"), match.group("ss"))
        end = timestamp_seconds(match.group("eh"), match.group("em"), match.group("es"))
        caption_text = clean_caption_text(lines[timing_index + 1 :])
        if caption_text and end > start:
            captions.append(caption_class(caption_text, start, end - start))

    if not captions:
        raise ValueError("WebVTT response contained no usable cues")
    return captions


def parse_json(payload: bytes) -> Any:
    return json.loads(payload.decode("utf-8-sig", errors="replace"))


def english_caption_candidates(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        for key in ("captions", "subtitles"):
            if isinstance(value.get(key), list):
                value = value[key]
                break
    if not isinstance(value, list):
        return []

    candidates = [item for item in value if isinstance(item, dict)]

    def language(item: dict[str, Any]) -> str:
        return str(
            item.get("languageCode")
            or item.get("code")
            or item.get("language")
            or item.get("label")
            or ""
        ).lower()

    candidates.sort(
        key=lambda item: (
            not language(item).startswith("en"),
            "auto" in str(item.get("label", "")).lower(),
        )
    )
    return candidates


def fetch_invidious(video_id: str, caption_class: type[Any], errors: list[str]) -> list[Any] | None:
    for instance in INVIDIOUS_INSTANCES:
        base = f"{instance}/api/v1/captions/{urllib.parse.quote(video_id)}"
        for language in ("en", "en-US", "en-GB"):
            url = f"{base}?lang={urllib.parse.quote(language)}"
            try:
                payload, content_type = request_bytes(url, "text/vtt, application/json;q=0.9, */*;q=0.5")
                if "json" not in content_type.lower() and payload.lstrip().upper().startswith(b"WEBVTT"):
                    return parse_webvtt(payload, caption_class)
                value = parse_json(payload)
                candidates = english_caption_candidates(value)
                for candidate in candidates:
                    candidate_url = candidate.get("url")
                    if isinstance(candidate_url, str) and candidate_url:
                        resolved = urllib.parse.urljoin(instance, candidate_url)
                        candidate_payload, _ = request_bytes(resolved, "text/vtt, */*;q=0.5")
                        return parse_webvtt(candidate_payload, caption_class)
            except Exception as exc:  # noqa: BLE001 - mirrors fail independently
                errors.append(f"Invidious {instance} ({language}): {type(exc).__name__}: {exc}")

        try:
            payload, _ = request_bytes(base, "application/json, */*;q=0.5")
            for candidate in english_caption_candidates(parse_json(payload)):
                candidate_url = candidate.get("url")
                if not isinstance(candidate_url, str) or not candidate_url:
                    label = candidate.get("label")
                    language = candidate.get("languageCode") or candidate.get("code")
                    query = urllib.parse.urlencode({key: value for key, value in (("label", label), ("lang", language)) if value})
                    candidate_url = f"{base}?{query}" if query else ""
                if candidate_url:
                    resolved = urllib.parse.urljoin(instance, candidate_url)
                    candidate_payload, _ = request_bytes(resolved, "text/vtt, */*;q=0.5")
                    return parse_webvtt(candidate_payload, caption_class)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Invidious {instance} (list): {type(exc).__name__}: {exc}")
    return None


def fetch_piped(video_id: str, caption_class: type[Any], errors: list[str]) -> list[Any] | None:
    for instance in PIPED_INSTANCES:
        try:
            payload, _ = request_bytes(f"{instance}/streams/{urllib.parse.quote(video_id)}", "application/json")
            value = parse_json(payload)
            candidates = english_caption_candidates(value)
            for candidate in candidates:
                candidate_url = candidate.get("url")
                if not isinstance(candidate_url, str) or not candidate_url:
                    continue
                resolved = urllib.parse.urljoin(instance, candidate_url)
                candidate_payload, _ = request_bytes(resolved, "text/vtt, */*;q=0.5")
                return parse_webvtt(candidate_payload, caption_class)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Piped {instance}: {type(exc).__name__}: {exc}")
    return None


def build_caption_fetcher(audit: Any):
    def fetch_captions(video_id: str) -> list[Any]:
        errors: list[str] = []
        captions = fetch_invidious(video_id, audit.Caption, errors)
        if captions:
            return captions
        captions = fetch_piped(video_id, audit.Caption, errors)
        if captions:
            return captions
        try:
            return audit.fetch_captions_direct(video_id)
        except AttributeError:
            try:
                return original_fetch(video_id)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Direct YouTube: {type(exc).__name__}: {exc}")
        raise RuntimeError("No caption provider succeeded. " + " | ".join(errors[-12:]))

    original_fetch = audit.fetch_captions
    return fetch_captions


def main() -> int:
    audit = load_audit_module()
    audit.fetch_captions = build_caption_fetcher(audit)
    return int(audit.main())


if __name__ == "__main__":
    raise SystemExit(main())
