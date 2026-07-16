#!/usr/bin/env python3
"""Run the statement audit using parallel caption-mirror requests."""

from __future__ import annotations

import concurrent.futures
import importlib.util
import sys
import threading
import urllib.parse
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "scripts" / "audit-exact-statement-clips.py"
MIRRORS_PATH = ROOT / "scripts" / "run-exact-statement-audit.py"
PROVIDER_TIMEOUT_SECONDS = 7


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    audit = load_module("falsology_exact_statement_audit", AUDIT_PATH)
    mirrors = load_module("falsology_caption_mirrors", MIRRORS_PATH)
    mirrors.TIMEOUT_SECONDS = PROVIDER_TIMEOUT_SECONDS

    preferred_lock = threading.Lock()
    preferred: list[tuple[str, str]] = []

    def parse_payload(payload: bytes, content_type: str) -> list[Any]:
        stripped = payload.lstrip()
        if stripped.upper().startswith(b"WEBVTT") or "vtt" in content_type.lower():
            return mirrors.parse_webvtt(payload, audit.Caption)
        value = mirrors.parse_json(payload)
        for candidate in mirrors.english_caption_candidates(value):
            candidate_url = candidate.get("url")
            if isinstance(candidate_url, str) and candidate_url:
                candidate_payload, _ = mirrors.request_bytes(candidate_url, "text/vtt, */*;q=0.5")
                return mirrors.parse_webvtt(candidate_payload, audit.Caption)
        raise ValueError("Provider returned no usable English captions")

    def fetch_invidious_instance(instance: str, video_id: str) -> list[Any]:
        base = f"{instance}/api/v1/captions/{urllib.parse.quote(video_id)}"
        errors: list[str] = []
        for url in (f"{base}?lang=en", base):
            try:
                payload, content_type = mirrors.request_bytes(
                    url,
                    "text/vtt, application/json;q=0.9, */*;q=0.5",
                )
                if url == base and not payload.lstrip().upper().startswith(b"WEBVTT"):
                    value = mirrors.parse_json(payload)
                    for candidate in mirrors.english_caption_candidates(value):
                        candidate_url = candidate.get("url")
                        if not isinstance(candidate_url, str) or not candidate_url:
                            query = urllib.parse.urlencode(
                                {
                                    key: value
                                    for key, value in (
                                        ("lang", candidate.get("languageCode") or candidate.get("code")),
                                        ("label", candidate.get("label")),
                                    )
                                    if value
                                }
                            )
                            candidate_url = f"{base}?{query}" if query else ""
                        if candidate_url:
                            resolved = urllib.parse.urljoin(instance, candidate_url)
                            candidate_payload, _ = mirrors.request_bytes(resolved, "text/vtt, */*;q=0.5")
                            return mirrors.parse_webvtt(candidate_payload, audit.Caption)
                    raise ValueError("Caption list had no usable English track")
                return parse_payload(payload, content_type)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{type(exc).__name__}: {exc}")
        raise RuntimeError("; ".join(errors[-2:]))

    def fetch_piped_instance(instance: str, video_id: str) -> list[Any]:
        payload, _ = mirrors.request_bytes(
            f"{instance}/streams/{urllib.parse.quote(video_id)}",
            "application/json",
        )
        value = mirrors.parse_json(payload)
        for candidate in mirrors.english_caption_candidates(value):
            candidate_url = candidate.get("url")
            if not isinstance(candidate_url, str) or not candidate_url:
                continue
            resolved = urllib.parse.urljoin(instance, candidate_url)
            candidate_payload, _ = mirrors.request_bytes(resolved, "text/vtt, */*;q=0.5")
            return mirrors.parse_webvtt(candidate_payload, audit.Caption)
        raise ValueError("Stream response had no usable English subtitle track")

    providers = [
        *(('invidious', instance) for instance in mirrors.INVIDIOUS_INSTANCES),
        *(('piped', instance) for instance in mirrors.PIPED_INSTANCES),
    ]

    def try_provider(provider: tuple[str, str], video_id: str) -> list[Any]:
        kind, instance = provider
        if kind == "invidious":
            return fetch_invidious_instance(instance, video_id)
        return fetch_piped_instance(instance, video_id)

    def fetch_captions(video_id: str) -> list[Any]:
        with preferred_lock:
            first_choice = preferred[0] if preferred else None

        errors: list[str] = []
        if first_choice is not None:
            try:
                return try_provider(first_choice, video_id)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"preferred {first_choice[1]}: {type(exc).__name__}: {exc}")

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=len(providers))
        futures = {executor.submit(try_provider, provider, video_id): provider for provider in providers}
        try:
            for future in concurrent.futures.as_completed(futures):
                provider = futures[future]
                try:
                    captions = future.result()
                    if captions:
                        with preferred_lock:
                            preferred[:] = [provider]
                        for pending in futures:
                            if pending is not future:
                                pending.cancel()
                        return captions
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{provider[1]}: {type(exc).__name__}: {exc}")
        finally:
            executor.shutdown(wait=True, cancel_futures=True)

        raise RuntimeError("No independent caption provider succeeded. " + " | ".join(errors[-10:]))

    audit.fetch_captions = fetch_captions
    return int(audit.main())


if __name__ == "__main__":
    raise SystemExit(main())
