from __future__ import annotations

import re
from backend.config import settings


# Patterns that must never appear in LLM output
_BLOCKED_OUTPUT_PATTERNS = [
    r"how to kill yourself",
    r"ways to die",
    r"self harm methods",
    r"best way to end my life",
    r"suicide method",
    r"hurt yourself safely",
]

# Helpline block — India-focused with international fallback
_HELPLINE_BLOCK = (
    "If you are in immediate danger, please reach out right now:\n\n"
    "• **AASRA (India):** +91-9820466626\n"
    "• **iCall (India):** +91-9152987821\n"
    "• **Kiran Mental Health Helpline:** 1800-599-0019 (free, 24/7)\n"
    "• **Vandrevala Foundation:** +91-1860-2662-345 (24/7)\n\n"
    "You can also text a trusted person in your life right now. "
    "You do not have to face this alone."
)


class SafetyService:

    def __init__(self):
        self.crisis_threshold  = settings.CRISIS_PROBABILITY_THRESHOLD
        self.override_threshold = settings.SAFETY_OVERRIDE_THRESHOLD

    def _blocked(self, text: str) -> bool:
        lowered = text.lower()
        return any(re.search(p, lowered) for p in _BLOCKED_OUTPUT_PATTERNS)

    def _active_crisis_response(self) -> str:
        return (
            "I hear you, and I'm genuinely concerned about you right now.\n\n"
            "What you're describing sounds like you may be in a very dark place, "
            "and I want you to know that your life has value — even when everything "
            "feels impossible.\n\n"
            "Right now, the most important thing is your safety. "
            "Please reach out to someone who can be with you or talk to you:\n\n"
            f"{_HELPLINE_BLOCK}\n\n"
            "Would you be willing to call or text one of these numbers right now?"
        )

    def _passive_crisis_response(self, llm_response: str) -> str:
        return (
            f"{llm_response}\n\n"
            "---\n"
            "I also want to gently check in — what you've shared sounds very heavy, "
            "and I want to make sure you're safe. If things ever feel like too much, "
            "please know that real support is available:\n\n"
            f"{_HELPLINE_BLOCK}"
        )

    def _moderate_support_addendum(self, llm_response: str) -> str:
        return (
            f"{llm_response}\n\n"
            "If these feelings continue or intensify, speaking with a licensed "
            "mental health professional can make a meaningful difference."
        )

    def validate_response(
        self,
        response: str,
        crisis_score: float,
        crisis_tier: str = "none",
    ) -> str:
        """
        Main safety entrypoint.

        Decision logic:
        - Active tier OR crisis_score >= override_threshold → full crisis override
        - Passive tier OR crisis_score >= crisis_threshold → LLM response + helpline append
        - Blocked content in LLM output → safe fallback
        - Moderate distress → LLM response + professional referral
        - Otherwise → return LLM response as-is
        """

        # Hard override: active intent or very high model score
        if crisis_tier == "active" or crisis_score >= self.override_threshold:
            return self._active_crisis_response()

        # High-risk: passive wish or model above threshold
        if crisis_tier == "passive" or crisis_score >= self.crisis_threshold:
            return self._passive_crisis_response(response)

        # LLM generated unsafe content
        if self._blocked(response):
            return (
                "I'm here to support you, and I want to make sure I'm giving you "
                "the safest guidance possible. If you're struggling right now, "
                "please consider reaching out to someone you trust or a mental "
                "health professional."
            )

        # Distress tier — soft professional referral
        if crisis_tier == "distress" or crisis_score >= 0.35:
            return self._moderate_support_addendum(response)

        return response