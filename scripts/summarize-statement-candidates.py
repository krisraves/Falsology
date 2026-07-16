#!/usr/bin/env python3
"""Write a compact human-review sheet from the transcript candidate report."""

from __future__ import annotations

import json
from pathlib import Path

SOURCE = Path("validation/statement-candidate-review.json")
OUTPUT = Path("validation/statement-candidate-summary.md")


def clean(value: object) -> str:
    return " ".join(str(value or "").split())


def main() -> int:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    cases = data.get("cases", {})
    failures = data.get("failures", {})
    lines = [
        "# Exact Statement Candidate Review",
        "",
        "Each candidate is a timestamped passage reconstructed from the source captions. Select only a passage clearly spoken by the named person.",
        "",
    ]

    for case_number in sorted(cases):
        case = cases[case_number]
        lines.extend(
            [
                f"## {case_number} — {clean(case.get('person'))} ({clean(case.get('verdict'))})",
                f"**Original:** {clean(case.get('claim'))}",
                f"**Video:** `{clean(case.get('videoId'))}` · duration {case.get('videoDurationSeconds')}s",
            ]
        )
        candidates = case.get("candidates") or []
        if not candidates:
            lines.append(f"**Status:** NO MATCH — {clean(failures.get(case_number, 'No viable candidate.'))}")
        else:
            for index, candidate in enumerate(candidates[:4], start=1):
                lines.append(
                    f"{index}. **{candidate.get('startSeconds')}–{candidate.get('endSeconds')}s** "
                    f"score {candidate.get('score')} · coverage {candidate.get('coverage')} — “{clean(candidate.get('text'))}”"
                )
                lines.append(f"   Context: {clean(candidate.get('context'))}")
        lines.append("")

    missing = sorted(set(failures) - set(cases))
    if missing:
        lines.extend(["# Sources Without Transcripts", ""])
        for case_number in missing:
            lines.append(f"- **{case_number}:** {clean(failures[case_number])}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
