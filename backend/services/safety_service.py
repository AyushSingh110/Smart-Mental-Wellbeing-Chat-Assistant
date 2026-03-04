from __future__ import annotations

import re
import logging
from backend.config import settings

logger = logging.getLogger(__name__)

# ── Helpline block ────────────────────────────────────────────────────────────
_HELPLINES = (
    "**AASRA (India):** +91-9820466626  \n"
    "**iCall (India):** +91-9152987821  \n"
    "**Kiran Helpline:** 1800-599-0019 *(free, 24 × 7)*  \n"
    "**Vandrevala Foundation:** +91-1860-2662-345 *(24 × 7)*"
)

# ── Crisis templates — LLM is never involved for these ───────────────────────
_ACTIVE_CRISIS = (
    "I hear you, and I'm genuinely worried about you right now. "
    "What you're describing sounds incredibly painful, and your life matters — "
    "even when everything feels impossible.\n\n"
    "Please reach out to someone who can be with you or talk to you right now:\n\n"
    f"{_HELPLINES}\n\n"
    "Would you be willing to call or text one of these numbers right now?"
)

_PASSIVE_CRISIS = (
    "That sounds like a really heavy thing to be carrying. "
    "I want you to know that what you're feeling is real, and you don't have to face it alone.\n\n"
    "Real support is available whenever you're ready:\n\n"
    f"{_HELPLINES}"
)

# ── Safe fallback when LLM fails ─────────────────────────────────────────────
_LLM_FALLBACK = (
    "I'm here with you. "
    "It sounds like things have been difficult lately, and I want you to feel heard. "
    "Take a breath — we can work through this together. "
    "What feels most pressing for you right now?"
)

_LLM_FALLBACK_HIGH_RISK = (
    "I hear you, and I want you to know that support is available. "
    "You don't have to go through this alone."
)

# ── Blocked output patterns (never appear in LLM output) ─────────────────────
_BLOCKED = [
    r"how to kill yourself",
    r"ways to die",
    r"self.?harm methods",
    r"best way to end my life",
    r"suicide method",
    r"hurt yourself safely",
]
_BLOCKED_RE = re.compile("|".join(_BLOCKED), re.IGNORECASE)

# ── Sentence target by category ───────────────────────────────────────────────
# (max sentences to keep — surplus trimmed from end)
_MAX_SENTENCES: dict[str, int] = {
    "Stable":            5,
    "Mild Stress":       4,
    "Moderate Distress": 3,
    "High Risk":         2,
    "Depression Risk":   2,
    "Crisis Risk":       0,   # 0 = never reaches trim (template used instead)
}


class SafetyService:

    def __init__(self):
        self.crisis_threshold   = settings.CRISIS_PROBABILITY_THRESHOLD
        self.override_threshold = settings.SAFETY_OVERRIDE_THRESHOLD

    # ── Main entry point ──────────────────────────────────────────────────────

    def validate_response(
        self,
        response: str,
        crisis_score: float,
        crisis_tier: str    = "none",
        category: str       = "Stable",
        llm_failed: bool    = False,
    ) -> str:
        """
        Decision flow:
          1. Active intent / very high score → predefined active crisis template
          2. Passive / high score            → predefined passive crisis template
          3. LLM failed                      → safe fallback (no error message)
          4. Blocked content in LLM output   → generic safe message
          5. All other tiers                 → trim to sentence target + optional referral
        """

        # ── 1. Hard crisis override — LLM skipped entirely ────────────────────
        if crisis_tier == "active" or crisis_score >= self.override_threshold:
            logger.info("SafetyService | ACTIVE CRISIS override triggered (tier=%s score=%.2f)",
                        crisis_tier, crisis_score)
            return _ACTIVE_CRISIS

        # ── 2. Passive crisis — predefined template ────────────────────────────
        if crisis_tier == "passive" or crisis_score >= self.crisis_threshold:
            logger.info("SafetyService | PASSIVE CRISIS override triggered (tier=%s score=%.2f)",
                        crisis_tier, crisis_score)
            return _PASSIVE_CRISIS

        # ── 3. LLM failure — safe fallback ────────────────────────────────────
        if llm_failed or not response or not response.strip():
            logger.warning("SafetyService | LLM failed — returning safe fallback (category=%s)",
                           category)
            if category in ("High Risk", "Depression Risk", "Crisis Risk"):
                return _LLM_FALLBACK_HIGH_RISK
            return _LLM_FALLBACK

        # ── 4. Blocked content ────────────────────────────────────────────────
        if _BLOCKED_RE.search(response):
            logger.warning("SafetyService | blocked content in LLM output")
            return (
                "I'm here to support you, and I want to make sure I give you "
                "the safest guidance possible. If you're struggling right now, "
                "please consider reaching out to someone you trust or a mental "
                "health professional."
            )

        # ── 5. Length control + optional referral ─────────────────────────────
        trimmed = self._trim_to_length(response, category)

        if crisis_tier == "distress" or crisis_score >= 0.35:
            trimmed += (
                "\n\nIf these feelings continue or intensify, speaking with a "
                "licensed mental health professional can make a real difference."
            )

        return trimmed

    # ── Length controller ─────────────────────────────────────────────────────

    @staticmethod
    def _trim_to_length(text: str, category: str) -> str:
        """
        Splits response into sentences and keeps only the first N,
        where N is determined by the category.
        Preserves paragraph structure where possible.
        """
        max_s = _MAX_SENTENCES.get(category, 5)
        if max_s == 0:
            return text   # crisis — handled above, but safe fallback

        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= max_s:
            return text   # already short enough

        kept = sentences[:max_s]
        result = " ".join(kept)

        # Ensure ends with proper punctuation
        if result and result[-1] not in ".!?":
            result += "."

        logger.debug(
            "SafetyService._trim_to_length | category=%s max=%d "
            "original=%d sentences kept=%d",
            category, max_s, len(sentences), len(kept),
        )
        return result

    # ── Standalone helpers (called by main.py for early-exit) ─────────────────

    @staticmethod
    def is_active_crisis(crisis_tier: str, crisis_score: float,
                         override_threshold: float) -> bool:
        return crisis_tier == "active" or crisis_score >= override_threshold

    @staticmethod
    def is_passive_crisis(crisis_tier: str, crisis_score: float,
                          crisis_threshold: float) -> bool:
        return crisis_tier == "passive" or crisis_score >= crisis_threshold
