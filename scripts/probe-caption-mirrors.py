#!/usr/bin/env python3
"""Extract browser-visible API calls from public transcript-tool bundles."""

from __future__ import annotations

import html.parser
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

OUTPUT = Path("validation/caption-provider-probe.json")
TIMEOUT = 20
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
SITES = (
    "https://youtube2text.diguardia.org/",
    "https://reel-stack.com/toolkit/youtube-transcript/",
    "https://transcripty.ai/",
    "https://transcriptgrab.com/",
)


class ScriptParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.scripts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "script":
            src = dict(attrs).get("src")
            if src:
                self.scripts.append(str(src))


def fetch_text(url: str, limit: int = 4_000_000) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/javascript,application/json;q=0.9,*/*;q=0.5",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.read(limit).decode("utf-8", errors="replace")


def compact(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\\/", "/")).strip()


def context_matches(text: str, pattern: re.Pattern[str], radius: int = 500, maximum: int = 100) -> list[str]:
    found: list[str] = []
    normalized = text.replace("\\/", "/")
    for match in pattern.finditer(normalized):
        value = compact(normalized[max(0, match.start() - radius) : min(len(normalized), match.end() + radius)])
        if value and value not in found:
            found.append(value)
        if len(found) >= maximum:
            break
    return found


def quoted_api_strings(text: str) -> list[str]:
    values: list[str] = []
    for match in re.finditer(r"[\"'`]([^\"'`]{2,350})[\"'`]", text.replace("\\/", "/")):
        value = match.group(1)
        lower = value.lower()
        if any(token in lower for token in ("/api/", "transcript", "caption", "subtitle", "supabase", "workers.dev", "vercel.app", "railway.app", "render.com")):
            value = compact(value)
            if value not in values:
                values.append(value)
        if len(values) >= 250:
            break
    return values


def inspect_site(site: str) -> dict[str, object]:
    result: dict[str, object] = {"site": site, "scripts": [], "errors": []}
    try:
        html = fetch_text(site)
        parser = ScriptParser()
        parser.feed(html)
        urls = [urllib.parse.urljoin(site, src) for src in parser.scripts]
        inspected: list[dict[str, object]] = []
        for url in urls[:30]:
            try:
                script = fetch_text(url)
                fetch_calls = context_matches(script, re.compile(r"\bfetch\s*\("), 700, 100)
                request_calls = context_matches(script, re.compile(r"(?i)(axios|XMLHttpRequest|\.post\(|\.get\(|invoke\(|functions\.invoke)"), 500, 100)
                strings = quoted_api_strings(script)
                if fetch_calls or request_calls or strings:
                    inspected.append(
                        {
                            "url": url,
                            "bytes": len(script.encode()),
                            "fetchContexts": fetch_calls,
                            "requestContexts": request_calls,
                            "apiStrings": strings,
                        }
                    )
            except Exception as exc:  # noqa: BLE001
                inspected.append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
        result["scripts"] = inspected
    except Exception as exc:  # noqa: BLE001
        result["errors"] = [f"{type(exc).__name__}: {exc}"]
    return result


def main() -> int:
    report = {"results": [inspect_site(site) for site in SITES]}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("API call extraction report written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
