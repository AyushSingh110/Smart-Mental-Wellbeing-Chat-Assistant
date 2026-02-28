"""
Mental Health Matrix service.

Computes TRS, MHI, and category from the five input signals:
  E  – Emotion risk score
  C  – Crisis probability
  S  – PHQ‑2 / GAD‑2 screening score (normalised)
  B  – Behavioral signal
  H  – Historical trend score
"""

from __future__ import annotations

import logging

from backend.config import settings
from backend.database.schemas import (
    CrisisResult,
    EmotionResult,
    MatrixResult,
    MentalHealthCategory,
)
from backend.utils.scoring import (
    categorize_mhi,
    compute_mhi,
    compute_trs,
    normalise_emotion_to_risk,
)

logger = logging.getLogger(__name__)


def calculate(
    emotion: EmotionResult,
    crisis: CrisisResult,
    screening_normalized: float,
    behavioral_score: float,
    historical_trend_score: float,
) -> MatrixResult:
    """
    Given the five component signals, compute TRS → MHI → category.
    Applies safety override when crisis probability exceeds threshold.
    """
    emotion_risk = normalise_emotion_to_risk(emotion.scores)

    trs = compute_trs(
        emotion_score=emotion_risk,
        crisis_probability=crisis.probability,
        screening_score=screening_normalized,
        behavioral_score=behavioral_score,
        historical_score=historical_trend_score,
    )

    mhi = compute_mhi(trs)
    category = categorize_mhi(mhi)

    # ── Safety override: force crisis category ──────────
    if crisis.safety_override:
        category = MentalHealthCategory.CRISIS.value
        mhi = min(mhi, 15.0)
        logger.warning("Matrix safety override → category forced to CRISIS (MHI=%.1f)", mhi)

    return MatrixResult(
        trs=trs,
        mhi=mhi,
        category=MentalHealthCategory(category),
        component_scores={
            "emotion_risk": emotion_risk,
            "crisis_probability": crisis.probability,
            "screening": screening_normalized,
            "behavioral": behavioral_score,
            "historical_trend": historical_trend_score,
        },
    )
