#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

script_path = Path(__file__).with_name("recover-archive-sources.py")
source = script_path.read_text(encoding="utf-8")
source = source.replace('f"ytsearch20:{query}"', 'f"ytsearch12:{query}"')
source = source.replace('timeout=110', 'timeout=75')
source = source.replace('timeout=55', 'timeout=32')
source = source.replace('for query in query_variants(person, claim):', 'for query in query_variants(person, claim)[:3]:')
source = source.replace(
    '        for candidate in results:\n            video_id = candidate["videoId"]',
    '        for candidate in results:\n            if len(checked) >= 16:\n                break\n            video_id = candidate["videoId"]',
)
source = source.replace('ThreadPoolExecutor(max_workers=8)', 'ThreadPoolExecutor(max_workers=12)')
exec(compile(source, str(script_path), "exec"), {"__name__": "__main__", "__file__": str(script_path)})
