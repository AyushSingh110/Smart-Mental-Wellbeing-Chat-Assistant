from __future__ import annotations
from backend.config import settings

_EMOTION_MULTIPLIERS = {
    "sadness": 1.25,
    "fear":    1.20,
    "anger":   1.15,
    "stress":  1.08,
    "anxiety": 1.08,
    "neutral": 0.55,
}

# MHI hard ceilings by crisis tier — no matter what other factors score,
# these ceilings prevent crisis language from staying in "Mild Stress"
_CRISIS_MHI_CEILINGS = {
    "active":   25.0,   # Crisis Risk
    "passive":  42.0,   # High Risk
    "distress": 62.0,   # Moderate Distress
    "none":    100.0,   # No ceiling
}


class MentalHealthMatrix:

    def __init__(self):
        self.weights = {
            "E": settings.WEIGHT_EMOTION,
            "C": settings.WEIGHT_CRISIS,
            "S": settings.WEIGHT_SCREENING,
            "B": settings.WEIGHT_BEHAVIORAL,
            "H": settings.WEIGHT_HISTORY,
        }

    def _adjust_emotion(self, label: str, score: float) -> float:
        return min(score * _EMOTION_MULTIPLIERS.get(label, 1.0), 1.0)

    def compute(
        self,
        emotion_score: float,
        crisis_score: float,
        emotion_label: str = "neutral",
        screening_score: float = 0.0,
        behavioral_score: float = 0.0,
        history_score: float = 0.5,
        crisis_tier: str = "none",
    ) -> float:
        adjusted_emotion = self._adjust_emotion(emotion_label, emotion_score)

        # Non-linear crisis amplification — steeper curve at high values
        boosted_crisis = crisis_score ** 0.60

        # Behavioral and screening scores amplify each other when both are elevated
        amplified_behavioral = behavioral_score * (1.0 + 0.4 * screening_score)
        amplified_screening  = screening_score  * (1.0 + 0.3 * behavioral_score)

        total_risk = (
            self.weights["E"] * adjusted_emotion +
            self.weights["C"] * boosted_crisis +
            self.weights["S"] * min(amplified_screening, 1.0) +
            self.weights["B"] * min(amplified_behavioral, 1.0) +
            self.weights["H"] * history_score
        )

        weight_sum = sum(self.weights.values())
        normalized_risk = total_risk / weight_sum
        raw_mhi = max(0.0, min(100.0, 100.0 * (1.0 - normalized_risk)))

        # Apply hard ceiling based on crisis tier — this is the critical fix
        ceiling = _CRISIS_MHI_CEILINGS.get(crisis_tier, 100.0)
        return round(min(raw_mhi, ceiling), 2)

    def categorize(self, mhi: float, crisis_score: float, crisis_tier: str = "none") -> str:
        # Hard category override for crisis tiers
        if crisis_tier == "active" or crisis_score >= 0.85:
            return "Crisis Risk"
        if crisis_tier == "passive" or crisis_score >= settings.CRISIS_PROBABILITY_THRESHOLD:
            return "High Risk"
        if mhi >= 80:
            return "Stable"
        if mhi >= 65:
            return "Mild Stress"
        if mhi >= 50:
            return "Moderate Distress"
        if mhi >= 35:
            return "High Risk"
        if mhi >= 20:
            return "Depression Risk"
        return "Crisis Risk"