from __future__ import annotations

import re
import logging
from backend.config import settings

logger = logging.getLogger(__name__)

# ── Emotion risk multipliers ──────────────────────────────────────────────────
_EMOTION_MULTIPLIERS = {
    "sadness": 1.30,
    "fear":    1.22,
    "anger":   1.15,
    "stress":  1.10,
    "anxiety": 1.10,
    "neutral": 0.45,   # neutrality → lower risk contribution
}

# ── Hard MHI ceilings by crisis tier ─────────────────────────────────────────
# "easier if I disappeared" → passive → MHI ≤ 35  → always "High Risk" or worse
_CRISIS_CEILINGS = {
    "active":   20.0,   # → always "Crisis Risk"
    "passive":  35.0,   # → always "High Risk"
    "distress": 58.0,   # → at most "Moderate Distress"
    "none":    100.0,
}

# ── Hopeless language patterns — extra direct MHI penalty ────────────────────
# These add a raw penalty on top of the weighted score
_HOPELESS_PATTERNS = re.compile(
    r"\b(hopeless|no\s+hope|pointless|nothing\s+matters|"
    r"what'?s\s+the\s+point|give\s+up|gave\s+up|"
    r"can'?t\s+go\s+on|can'?t\s+do\s+this\s+anymore|"
    r"disappear|disappeared|wish\s+i\s+(was|were)\s+(gone|dead|never\s+born)|"
    r"easier\s+if\s+i\s+(just\s+)?(was\s+gone|disappeared|wasn'?t\s+here)|"
    r"burden\s+to\s+(everyone|others|my\s+family)|"
    r"nobody\s+(cares|would\s+miss\s+me))\b",
    re.IGNORECASE,
)

# How many hopeless signals to count (each adds penalty)
_HOPELESS_PENALTY_PER_MATCH = 6.0   # MHI points to deduct per matched phrase
_HOPELESS_MAX_PENALTY       = 24.0  # cap at 4 phrases × 6 points


class MentalHealthMatrix:

    def __init__(self):
        self.weights = {
            "E": settings.WEIGHT_EMOTION,
            "C": settings.WEIGHT_CRISIS,
            "S": settings.WEIGHT_SCREENING,
            "B": settings.WEIGHT_BEHAVIORAL,
            "H": settings.WEIGHT_HISTORY,
        }
        logger.debug("MentalHealthMatrix | weights: %s", self.weights)

    # ── Public API ────────────────────────────────────────────────────────────

    def compute(
        self,
        emotion_score: float,
        crisis_score: float,
        emotion_label: str    = "neutral",
        screening_score: float = 0.0,
        behavioral_score: float = 0.0,
        history_score: float   = 0.5,
        crisis_tier: str       = "none",
        raw_text: str          = "",   # optional — enables hopeless-language penalty
    ) -> float:
        """
        Returns MHI in [0, 100].  Lower = worse mental health.

        Key changes vs original:
          1. crisis_score^0.50  (more aggressive than ^0.60)
          2. Direct large penalty when crisis_score > 0.6
          3. Hopeless-language penalty from raw_text scan
          4. Hard ceiling tightened (passive → 35, not 42)
        """

        # 1. Adjusted emotion
        emotion_adj = min(emotion_score * _EMOTION_MULTIPLIERS.get(emotion_label, 1.0), 1.0)

        # 2. Nonlinear crisis amplification — steeper than before
        crisis_amp = crisis_score ** 0.50   # 0.9 → 0.949,  0.65 → 0.806

        # 3. Behavioral + screening cross-amplification
        behavioral_amp = min(behavioral_score * (1.0 + 0.5 * screening_score), 1.0)
        screening_amp  = min(screening_score  * (1.0 + 0.3 * behavioral_score), 1.0)

        # 4. Weighted risk total
        total_risk = (
            self.weights["E"] * emotion_adj   +
            self.weights["C"] * crisis_amp    +
            self.weights["S"] * screening_amp +
            self.weights["B"] * behavioral_amp +
            self.weights["H"] * history_score
        )

        weight_sum     = sum(self.weights.values())
        normalized     = total_risk / weight_sum
        raw_mhi        = max(0.0, min(100.0, 100.0 * (1.0 - normalized)))

        # 5. Direct large penalty when crisis_score is high (fixes the MHI=42 bug)
        #    crisis_score=0.65 → -26 pts,  crisis_score=0.80 → -40 pts
        if crisis_score > 0.6:
            penalty  = (crisis_score - 0.6) / 0.4 * 50.0   # 0→50 pts as score goes 0.6→1.0
            raw_mhi  = max(0.0, raw_mhi - penalty)

        # 6. Hopeless-language scan (optional, only when raw_text provided)
        if raw_text:
            matches      = len(_HOPELESS_PATTERNS.findall(raw_text))
            hop_penalty  = min(matches * _HOPELESS_PENALTY_PER_MATCH, _HOPELESS_MAX_PENALTY)
            raw_mhi      = max(0.0, raw_mhi - hop_penalty)

        # 7. Hard ceiling by crisis tier
        ceiling = _CRISIS_CEILINGS.get(crisis_tier, 100.0)
        final   = round(min(raw_mhi, ceiling), 2)

        logger.debug(
            "MHI | emotion=%.2f(%s) crisis=%.2f(%s) beh=%.2f screen=%.2f "
            "hist=%.2f → raw=%.1f → final=%.1f",
            emotion_score, emotion_label, crisis_score, crisis_tier,
            behavioral_score, screening_score, history_score,
            raw_mhi + (min(len(_HOPELESS_PATTERNS.findall(raw_text)) * _HOPELESS_PENALTY_PER_MATCH,
                           _HOPELESS_MAX_PENALTY) if raw_text else 0),
            final,
        )
        return final

    def categorize(self, mhi: float, crisis_score: float, crisis_tier: str = "none") -> str:
        """
        Hard overrides for crisis tiers first, then MHI bands.
        Thresholds tightened compared to original.
        """
        if crisis_tier == "active"  or crisis_score >= 0.85:
            return "Crisis Risk"
        if crisis_tier == "passive" or crisis_score >= settings.CRISIS_PROBABILITY_THRESHOLD:
            return "High Risk"

        # MHI bands (tightened — higher bar for "Stable")
        if mhi >= 80:   return "Stable"
        if mhi >= 65:   return "Mild Stress"
        if mhi >= 50:   return "Moderate Distress"
        if mhi >= 30:   return "High Risk"
        if mhi >= 15:   return "Depression Risk"
        return "Crisis Risk"
