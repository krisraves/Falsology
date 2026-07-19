#!/usr/bin/env python3
"""Run the content builder with reliable public YouTube embed checks."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import requests

SCRIPT = Path(__file__).with_name("build-verified-content-deck.py")
spec = importlib.util.spec_from_file_location("falsology_content_builder", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load content builder")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def youtube_public_metadata(video_id: str) -> dict[str, Any] | None:
    """Confirm a public YouTube watch page without scanning generic UI strings.

    YouTube's embed HTML includes localized text for every possible error state,
    even when a video is playable. The previous checker therefore rejected all
    candidates. A successful oEmbed response plus a reachable embed page is the
    stable public check available without a YouTube Data API credential.
    """
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        response = requests.get(oembed_url, headers=module.HEADERS, timeout=module.HTTP_TIMEOUT)
        if response.status_code != 200:
            return None
        data = response.json()
        embed_response = requests.get(
            f"https://www.youtube.com/embed/{video_id}?hl=en",
            headers=module.HEADERS,
            timeout=module.HTTP_TIMEOUT,
        )
        if embed_response.status_code >= 400:
            return None
        return {
            "title": str(data.get("title") or ""),
            "channel": str(data.get("author_name") or "YouTube source channel"),
            "embeddable": True,
        }
    except Exception:
        return None


module.youtube_public_metadata = youtube_public_metadata
exit_code = module.main()

if module.REPORT_PATH.exists():
    report = json.loads(module.REPORT_PATH.read_text(encoding="utf-8"))
    report["methodVersion"] = 2
    report["embedCheck"] = "YouTube oEmbed plus reachable embed endpoint"
    module.REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

raise SystemExit(exit_code)
