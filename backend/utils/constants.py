"""
Application‑wide constants.
"""

# ── Emotion labels (GoEmotions → mapped subset) ─────
EMOTION_LABELS: list[str] = [
    "neutral",
    "joy",
    "sadness",
    "anger",
    "fear",
    "stress",
    "anxiety",
    "disgust",
    "surprise",
]

# ── Intent labels ────────────────────────────────────
INTENT_LABELS: list[str] = [
    "venting",
    "advice_seeking",
    "crisis",
    "casual_talk",
    "assessment",
]

# ── Crisis keywords (rule‑based fallback) ───────────
CRISIS_KEYWORDS: list[str] = [
    "suicide",
    "suicidal",
    "kill myself",
    "end my life",
    "want to die",
    "no reason to live",
    "self-harm",
    "self harm",
    "cutting myself",
    "overdose",
    "jump off",
    "hang myself",
    "don't want to be alive",
    "hurting myself",
    "not worth living",
    "better off dead",
    "end it all",
]

# ── MHI category thresholds ─────────────────────────
MHI_THRESHOLDS: dict[str, tuple[float, float]] = {
    "normal": (80.0, 100.0),
    "mild_stress": (60.0, 79.99),
    "anxiety": (40.0, 59.99),
    "depression_risk": (20.0, 39.99),
    "crisis": (0.0, 19.99),
}

# ── Safety messages ──────────────────────────────────
CRISIS_ESCALATION_MESSAGE: str = (
    "I'm really concerned about what you've shared. "
    "You're not alone, and help is available right now.\n\n"
    "📞 **National Suicide Prevention Lifeline:** 988 (US)\n"
    "📞 **Crisis Text Line:** Text HOME to 741741\n"
    "📞 **International Association for Suicide Prevention:** "
    "https://www.iasp.info/resources/Crisis_Centres/\n\n"
    "Please reach out to a professional. Your life matters."
)
