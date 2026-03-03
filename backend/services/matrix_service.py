from __future__ import annotations

from backend.config import settings


# Negative emotion labels increase risk; neutral reduces it
_HIGH_RISK_EMOTIONS = {"sadness", "fear", "anger"}
_MODERATE_RISK_EMOTIONS = {"stress", "anxiety"}
_LOW_RISK_EMOTIONS = {"neutral"}

# Per-emotion multipliers applied to the raw emotion score
_EMOTION_MULTIPLIERS = {
    "sadness": 1.20,
    "fear":    1.15,
    "anger":   1.10,
    "stress":  1.05,
    "anxiety": 1.05,
    "neutral": 0.60,
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

    def _adjust_emotion(self, emotion_label: str, emotion_score: float) -> float:
        multiplier = _EMOTION_MULTIPLIERS.get(emotion_label, 1.0)
        return min(emotion_score * multiplier, 1.0)

    def compute(
        self,
        emotion_score: float,
        crisis_score: float,
        emotion_label: str = "neutral",
        screening_score: float = 0.0,
        behavioral_score: float = 0.0,
        history_score: float = 0.5,
    ) -> float:
        """
        Computes the Mental Health Index (MHI) on a [0, 100] scale.
        Higher MHI = better mental health.

        Parameters
        ----------
        emotion_score     : Raw probability from EmotionService [0, 1]
        crisis_score      : Risk probability from CrisisService [0, 1]
        emotion_label     : Dominant emotion label (used for multiplier)
        screening_score   : Normalized PHQ-2/GAD-2 score from ScreeningService [0, 1]
        behavioral_score  : Risk score from BehavioralService [0, 1]
        history_score     : Trend-weighted risk from HistoryService [0, 1]
        """
        adjusted_emotion = self._adjust_emotion(emotion_label, emotion_score)

        # Crisis score gets a non-linear boost at high values
        boosted_crisis = crisis_score ** 0.75

        total_risk = (
            self.weights["E"] * adjusted_emotion +
            self.weights["C"] * boosted_crisis +
            self.weights["S"] * screening_score +
            self.weights["B"] * behavioral_score +
            self.weights["H"] * history_score
        )

        # Normalize weights sum to validate (defensive)
        weight_sum = sum(self.weights.values())
        normalized_risk = total_risk / weight_sum

        mhi = max(0.0, min(100.0, 100.0 * (1.0 - normalized_risk)))
        return round(mhi, 2)

    def categorize(self, mhi: float, crisis_score: float) -> str:
        if crisis_score >= settings.CRISIS_PROBABILITY_THRESHOLD:
            return "Crisis"
        if mhi >= 80:
            return "Normal"
        if mhi >= 65:
            return "Mild Stress"
        if mhi >= 50:
            return "Moderate Stress"
        if mhi >= 35:
            return "Anxiety Risk"
        if mhi >= 20:
            return "Depression Risk"
        return "Crisis"
