"""
Safety validation service – post‑generation guardrail layer.

Scans the LLM output for harmful content before it reaches the user.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Phrases that must NEVER appear in bot responses
_BLOCKED_PATTERNS: list[str] = [
    r"you should (kill|hurt|harm) yourself",
    r"(commit|attempt) suicide",
    r"here('s| is) how to (end|take) your life",
    r"(instructions|steps) (to|for) (self[- ]?harm|suicide|overdose)",
    r"you('re| are) (hopeless|worthless|better off dead)",
    r"nobody (cares|will miss you)",
    r"prescription|prescribe|medication dosage",
    r"diagnos(e|is|ing) you with",
]

_compiled = [re.compile(p, re.IGNORECASE) for p in _BLOCKED_PATTERNS]


def validate_response(text: str) -> tuple[str, bool]:
    """
    Scan *text* for harmful patterns.
    Returns (safe_text, was_flagged).
    If flagged, the harmful portion is redacted and replaced with a safe default.
    """
    flagged = False
    for pattern in _compiled:
        if pattern.search(text):
            logger.warning("Safety filter triggered on pattern: %s", pattern.pattern)
            flagged = True
            break

    if flagged:
        safe_text = (
            "I want to make sure I'm supporting you in a helpful way. "
            "It's important to talk to a qualified mental health professional "
            "who can provide personalized guidance. "
            "Would you like me to share some resources?"
        )
        return safe_text, True

    return text, False
