#!/usr/bin/env python3
"""Inspect public transcript tools for browser-visible API endpoints."""

from __future__ import annotations

import concurrent.futures
import html.parser
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

OUTPUT = Path("validation/caption-provider-probe.json")
TIMEOUT = 15
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
SITES = (
    "https://youtube2text.diguardia.org/",
    "https://reel-stack.com/toolkit/youtube-transcript/",
    "https://transcripty.ai/",
    "https://transcriptgrab.com/",
    "https://toolerbox.com/youtube-transcript/",
    "https://speedytools.dev/tools/youtube-transcript",
)

INTERESTING = re.compile(
    r"(?i)(?:https?://[^\"'`\s)]+|/[a-z0-9_./?=&%${}:-]{3,})"
    r"(?=[^\n]{0,120}(?:transcript|caption|subtitle|youtube|transcrib))"
)
KEYWORDS = re.compile(r"(?i)(transcript|caption|subtitle|youtube|transcrib|/api/)")


class ScriptParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.scripts: list[str] = []
        self.inline: list[str] = []
        self._inside_script = False
        self._buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "script":
            return
        self._inside_script = True
        values = dict(attrs)
        if values.get("src"):
            self.scripts.append(str(values["src"]))

    def handle_data(self, data: str) -> None:
        if self._inside_script:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "script":
            return
        if self._buffer:
            self.inline.append("".join(self._buffer))
        self._buffer = []
        self._inside_script = False


def fetch(url: str, limit: int = 2_000_000) -> tuple[int, str, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/javascript,application/json;q=0.9,*/*;q=0.5",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        payload = response.read(limit)
        return response.status, response.headers.get("Content-Type", ""), payload.decode("utf-8", errors="replace")


def snippets(text: str, maximum: int = 80) -> list[str]:
    found: list[str] = []
    compact = text.replace("\\/", "/")
    for match in KEYWORDS.finditer(compact):
        start = max(0, match.start() - 180)
        end = min(len(compact), match.end() + 300)
        value = re.sub(r"\s+", " ", compact[start:end]).strip()
        if value and value not in found:
            found.append(value)
        if len(found) >= maximum:
            break
    return found


def inspect_site(site: str) -> dict[str, object]:
    result: dict[str, object] = {"site": site, "scripts": [], "inlineSnippets": [], "errors": []}
    try:
        status, content_type, body = fetch(site)
        result.update({"status": status, "contentType": content_type, "htmlBytes": len(body.encode())})
        parser = ScriptParser()
        parser.feed(body)
        result["inlineSnippets"] = snippets("\n".join(parser.inline), 30)
        script_urls = [urllib.parse.urljoin(site, src) for src in parser.scripts][:30]

        def inspect_script(url: str) -> dict[str, object]:
            try:
                script_status, script_type, script_body = fetch(url)
                matches = snippets(script_body, 50)
                return {
                    "url": url,
                    "status": script_status,
                    "contentType": script_type,
                    "bytes": len(script_body.encode()),
                    "snippets": matches,
                }
            except Exception as exc:  # noqa: BLE001
                return {"url": url, "error": f"{type(exc).__name__}: {exc}"}

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(12, max(1, len(script_urls)))) as executor:
            result["scripts"] = list(executor.map(inspect_script, script_urls))
    except Exception as exc:  # noqa: BLE001
        result["errors"] = [f"{type(exc).__name__}: {exc}"]
    return result


def main() -> int:
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(SITES)) as executor:
        results = list(executor.map(inspect_site, SITES))
    report = {"results": results}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Endpoint discovery report written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
