from __future__ import annotations

import re
from backend.config import settings


# Weighted pattern groups — each group represents a behavioral risk dimension.
# Scores are normalized to [0, 1] before returning.

_PATTERNS: list[tuple[str, float]] = [
    # Social withdrawal
    (r"\b(isolat(e|ed|ing)|withdrew|withdrawn|avoid(ing)? (people|others|friends|family))\b", 0.75),
    (r"\b(don'?t want to (see|talk|meet)|stay(ing)? home|lock(ed)? myself)\b", 0.65),

    # Activity avoidance
    (r"\b(stopped (going|working|exercising|eating|sleeping)|can'?t (get up|function|do anything))\b", 0.70),
    (r"\b(no (motivation|energy|interest)|lost interest|don'?t enjoy)\b", 0.60),

    # Negative coping
    (r"\b(drink(ing)?|alcohol|smok(e|ing)|using drugs?|can'?t stop eating)\b", 0.65),
    (r"\b(binge|purge|starv(e|ing)|not eat(ing)?)\b", 0.70),

    # Behavioral despair signals
    (r"\b(giv(e|ing) up|what'?s the point|nothing matters|pointless|hopeless)\b", 0.80),
    (r"\b(can'?t (sleep|focus|concentrate)|insomnia|nightmares)\b", 0.55),

    # Self-neglect
    (r"\b(don'?t (shower|eat|leave (bed|house))|stopped (caring|trying))\b", 0.70),
]

_MAX_POSSIBLE = sum(w for _, w in _PATTERNS)


class BehavioralService:

    def predict(self, text: str) -> float:
        """
        Returns a behavioral risk score in [0, 1].
        Higher = more behavioral risk signals detected.
        """
        lowered = text.lower()
        raw = 0.0

        for pattern, weight in _PATTERNS:
            if re.search(pattern, lowered):
                raw += weight

        return round(min(raw / _MAX_POSSIBLE, 1.0), 4)
