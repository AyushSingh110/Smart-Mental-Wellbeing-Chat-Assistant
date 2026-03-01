import re
from backend.config import settings


class SafetyService:
    """
    Final safety validation layer before returning response to user.
    Ensures crisis override and prevents unsafe output.
    """

    def __init__(self):
        self.crisis_threshold = settings.CRISIS_PROBABILITY_THRESHOLD
        self.override_threshold = settings.SAFETY_OVERRIDE_THRESHOLD

        # Patterns that should NEVER appear in final output
        self.blocked_patterns = [
            r"how to kill yourself",
            r"ways to die",
            r"self harm methods",
            r"best way to end my life",
            r"suicide method",
            r"hurt yourself safely",
        ]

    def _contains_blocked_content(self, text: str) -> bool:
        """
        Check if LLM response contains unsafe patterns.
        """
        text_lower = text.lower()

        for pattern in self.blocked_patterns:
            if re.search(pattern, text_lower):
                return True

        return False

    def _crisis_override_message(self) -> str:
        """
        Emergency override response for high-risk users.
        """
        return (
            "I'm really concerned about your safety right now.\n\n"
            "If you're in immediate danger, please contact emergency services "
            "or a suicide prevention hotline immediately.\n\n"
            "In India, you can call:\n"
            "• AASRA: +91-9820466726\n"
            "• Kiran (Mental Health Helpline): 1800-599-0019\n\n"
            "You deserve real-time human support. "
            "Would you be willing to reach out to someone right now?"
        )

    def validate_response(self, response: str, crisis_score: float) -> str:
        """
        Main safety entrypoint.
        Applies crisis override and content filtering.
        """

        # Hard crisis override
        if crisis_score >= self.override_threshold:
            return self._crisis_override_message()

        #If moderate crisis — reinforce professional help
        if crisis_score >= self.crisis_threshold:
            return (
                response
                + "\n\nIt may be helpful to consider speaking with a licensed "
                  "mental health professional for additional support."
            )

        # Check for unsafe generated content
        if self._contains_blocked_content(response):
            return (
                "I'm here to support you, but I can't provide harmful or unsafe information. "
                "If you're struggling, please consider reaching out to a trusted person "
                "or a mental health professional."
            )

        # Otherwise safe
        return response