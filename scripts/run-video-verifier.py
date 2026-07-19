#!/usr/bin/env python3
"""Run the candidate verifier with stricter language matching patches."""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

SCRIPT = Path(__file__).with_name("verify-video-candidates.py")
spec = importlib.util.spec_from_file_location("falsology_video_verifier", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load candidate verifier")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Negation is materially important to truth/lie statements and must remain in
# the lexical comparison. Avoid loose pronoun patterns such as `were` or `ill`.
module.MATCH_STOP_WORDS.discard("not")
module.MATCH_STOP_WORDS.discard("never")
module.FIRST_PERSON = re.compile(
    r"\b(i|i'm|im|i've|ive|i'd|i'll|me|my|mine|we|we're|weve|we've|our|ours)\b",
    re.I,
)

raise SystemExit(module.main())
