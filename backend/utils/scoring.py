"""
Scoring utilities for the Mental Health Matrix and assessments.
"""

from __future__ import annotations

from backend.config import settings
from backend.utils.constants import MHI_THRESHOLDS


def compute_trs(
    emotion_score: float,
    crisis_probability: float,
    screening_score: float,
    behavioral_score: float,
    historical_score: float,
) -> float:
    """
    Total Risk Score:
        TRS = w1·E + w2·C + w3·S + w4·B + w5·H
    All inputs should be normalised to [0, 1].
    """
    trs = (
        settings.WEIGHT_EMOTION * emotion_score
        + settings.WEIGHT_CRISIS * crisis_probability
        + settings.WEIGHT_SCREENING * screening_score
        + settings.WEIGHT_BEHAVIORAL * behavioral_score
        + settings.WEIGHT_HISTORY * historical_score
    )
    return round(max(0.0, min(1.0, trs)), 4)


def compute_mhi(trs: float) -> float:
    """Mental Health Index: MHI = 100 × (1 − TRS)"""
    return round(100.0 * (1.0 - trs), 2)


def categorize_mhi(mhi: float) -> str:
    """Map MHI to a named mental‑health category string."""
    for category, (low, high) in MHI_THRESHOLDS.items():
        if low <= mhi <= high:
            return category
    return "crisis"  # default to safest bucket


def normalise_emotion_to_risk(emotion_scores: dict[str, float]) -> float:
    """
    Convert the emotion probability vector into a single 0‑1 risk score.
    Negative emotions contribute positively to risk.
    """
    negative_labels = {"sadness", "anger", "fear", "stress", "anxiety", "disgust"}
    risk = sum(v for k, v in emotion_scores.items() if k in negative_labels)
    return round(max(0.0, min(1.0, risk)), 4)


def normalise_screening(phq2: int | None, gad2: int | None) -> float:
    """
    Normalise combined PHQ‑2 (0‑6) + GAD‑2 (0‑6) into [0, 1].
    Max combined = 12.
    """
    total = (phq2 or 0) + (gad2 or 0)
    return round(total / 12.0, 4)
