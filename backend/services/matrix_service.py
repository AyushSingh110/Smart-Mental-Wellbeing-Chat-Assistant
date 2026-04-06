from __future__ import annotations

import re
import logging
from backend.config import settings

logger = logging.getLogger(__name__)

# ── Emotion risk multipliers
_EMOTION_MUL: dict[str, float] = {
    "sadness": 1.35,
    "fear":    1.25,
    "anxiety": 1.18,
    "stress":  1.12,
    "anger":   1.15,
    "neutral": 0.40,
}

# ── Hard MHI ceilings per crisis tier
# Applied AFTER all computation. MHI cannot exceed these values.
_CRISIS_CEIL: dict[str, float] = {
    "active":   18.0,   # always "Crisis Risk"
    "passive":  33.0,   # always "High Risk"
    "distress": 56.0,   # at most "Moderate Distress"
    "none":    100.0,
}

# ── 7-band MHI category thresholds (descending, first match wins)
_MHI_BANDS: list[tuple[float, str]] = [
    (88.0, "Flourishing"),
    (75.0, "Stable"),
    (62.0, "Mild Stress"),
    (48.0, "Moderate Distress"),
    (34.0, "High Risk"),
    (18.0, "Severe Risk"),
    (0.0,  "Crisis Risk"),
]

# ── Hopeless / disappearance language patterns
# Each MATCH deducts 6 MHI points (max 4 matches = 24 pts)
_HOPELESS = re.compile(
    r"\b("
    # Direct death / disappearance wish
    r"disappear|disappeared|"
    r"wish\s+i\s+(was|were)\s+(gone|dead|never\s+born)|"
    r"easier\s+if\s+i\s+(just\s+)?(was\s+gone|disappeared|wasn'?t\s+here|wasn'?t\s+alive)|"
    r"better\s+off\s+(without\s+me|if\s+i\s+(was|were)\s+gone)|"
    r"want\s+to\s+(die|end\s+it|disappear)|"
    # Hopelessness
    r"hopeless|no\s+hope|what'?s\s+the\s+point|nothing\s+matters|pointless|"
    r"give\s+up|gave\s+up|can'?t\s+go\s+on|can'?t\s+do\s+this\s+anymore|"
    r"no\s+reason\s+to\s+(live|go\s+on)|"
    # Isolation / burden language
    r"nobody\s+(cares|would\s+miss\s+me|loves\s+me)|"
    r"(i'?m\s+a\s+)?burden\s+to\s+(everyone|others|my\s+family|them)|"
    # Emptiness
    r"feel\s+(completely\s+)?(empty|numb|hollow)|"
    r"nothing\s+left\s+(for\s+me|to\s+live\s+for)"
    r")\b",
    re.IGNORECASE,
)

_HOPELESS_PTS_PER_MATCH = 6.0
_HOPELESS_MAX_PEN       = 24.0   # cap at 4 matches

# ── Positive indicator patterns (bonus MHI points)
_POSITIVE_INDICATORS = re.compile(
    r"\b("
    r"(feeling|feel)\s+(better|good|great|grateful|hopeful|optimistic)|"
    r"(had\s+a\s+good\s+day|nice\s+day|beautiful\s+day)|"
    r"(grateful|thankful|blessed|appreciat(e|ed|ing))|"
    r"(progressing|improving|getting\s+better|on\s+the\s+mend)|"
    r"(meditation|meditated|mindfulness|breathing\s+exercise|went\s+for\s+a\s+(walk|run|jog))|"
    r"(talked\s+to\s+(a\s+friend|my\s+family|someone)|connected\s+with)|"
    r"(accomplished|achieved|proud\s+of|succeeded|made\s+progress)|"
    r"(slept\s+well|good\s+sleep|rested\s+well|ate\s+(well|healthy))"
    r")\b",
    re.IGNORECASE,
)

_POSITIVE_BASE_BONUS = 5.0   # base bonus for positive indicators
_POSITIVE_MAX_BONUS  = 8.0   # cap

# ── Linguistic complexity bonus (longer, structured thought = engagement)
_MIN_WORDS_FOR_COMPLEXITY = 20
_COMPLEXITY_BONUS = 3.0       # awarded when message is complex and coherent

# ── Consistency bonus: awarded when message length >= 15 words and non-crisis
_CONSISTENCY_THRESHOLD = 15
_CONSISTENCY_BONUS = 3.0

# ── Emotions that trigger persistence penalty when sustained across turns
_HIGH_RISK_EMOTIONS     = {"sadness", "fear", "anxiety"}
_PERSISTENCE_PEN        = 8.0    # pts deducted when last N turns all high-risk
_PERSISTENCE_WINDOW     = 3      # look back this many turns


class MentalHealthMatrix:

    def __init__(self):
        self.weights = {
            "E": settings.WEIGHT_EMOTION,
            "C": settings.WEIGHT_CRISIS,
            "S": settings.WEIGHT_SCREENING,
            "B": settings.WEIGHT_BEHAVIORAL,
            "H": settings.WEIGHT_HISTORY,
        }
        logger.debug("MentalHealthMatrix | weights=%s", self.weights)

    # ── Public API

    def compute(
        self,
        emotion_score:     float,
        crisis_score:      float,
        emotion_label:     str           = "neutral",
        screening_score:   float         = 0.0,
        behavioral_score:  float         = 0.0,
        history_score:     float         = 0.5,
        crisis_tier:       str           = "none",
        raw_text:          str           = "",
        recent_emotions:   list[str] | None = None,   # last N emotion labels
        mhi_trend:         list[float] | None = None, # last N MHI scores oldest→newest
        emotion_complexity: float        = 0.0,       # from EmotionFullResult
        suppression_flagged: bool        = False,      # from EmotionFullResult
    ) -> float:
        """
        Returns MHI ∈ [0, 100].  Lower = more at risk.

        Parameters
        ──────────
        recent_emotions    : emotion labels from the last few turns (for persistence penalty)
        mhi_trend          : MHI scores from the last few turns (for trend amplification)
        emotion_complexity : std-dev of top-3 emotion scores (0=pure, high=mixed/ambiguous)
        suppression_flagged: masking/suppression detected by emotion service
        """
        # Step 1 — Emotion risk adjustment
        emotion_adj = min(emotion_score * _EMOTION_MUL.get(emotion_label, 1.0), 1.0)

        # Step 2 — Nonlinear crisis amplification (exponent 0.45 → steeper than 0.50)
        crisis_amp = crisis_score ** 0.45

        # Step 3 — Behavioral × screening cross-amplification
        behavioral_amp = min(behavioral_score * (1.0 + 0.55 * screening_score), 1.0)
        screening_amp  = min(screening_score  * (1.0 + 0.35 * behavioral_score), 1.0)

        # Step 4 — History with trend multiplier
        adjusted_history = self._trend_history(history_score, mhi_trend)

        # Step 5 — Weighted risk total → raw MHI
        total_risk = (
            self.weights["E"] * emotion_adj      +
            self.weights["C"] * crisis_amp       +
            self.weights["S"] * screening_amp    +
            self.weights["B"] * behavioral_amp   +
            self.weights["H"] * adjusted_history
        )
        weight_sum = sum(self.weights.values())
        normalized = total_risk / weight_sum
        raw_mhi    = max(0.0, min(100.0, 100.0 * (1.0 - normalized)))

        # Step 6 — Quadratic direct penalty above 0.55 threshold (FIXED)
        # Bug fix: for crisis_score > 0.60, ensure minimum penalty of 25 pts
        if crisis_score > 0.55:
            excess  = (crisis_score - 0.55) / 0.45      # 0→1 as score goes 0.55→1.0
            penalty = (excess ** 1.5) * 55.0             # quadratic, max ~55 pts
            if crisis_score > 0.60:
                penalty = max(penalty, 25.0)             # fix: min 25 pts for score > 0.60
            raw_mhi = max(0.0, raw_mhi - penalty)
            logger.debug("Crisis penalty: score=%.2f excess=%.2f pen=%.1f", crisis_score, excess, penalty)

        # Step 7 — Hopeless-language scan
        hop_pen = 0.0
        if raw_text:
            matches = len(_HOPELESS.findall(raw_text))
            hop_pen = min(matches * _HOPELESS_PTS_PER_MATCH, _HOPELESS_MAX_PEN)
            raw_mhi = max(0.0, raw_mhi - hop_pen)
            if hop_pen > 0:
                logger.debug("Hopeless penalty: %d matches = %.0f pts", matches, hop_pen)

        # Step 8 — Emotional persistence penalty
        if recent_emotions and len(recent_emotions) >= _PERSISTENCE_WINDOW:
            last_n = recent_emotions[-_PERSISTENCE_WINDOW:]
            if all(e in _HIGH_RISK_EMOTIONS for e in last_n):
                raw_mhi = max(0.0, raw_mhi - _PERSISTENCE_PEN)
                logger.debug("Persistence penalty: %.0f pts (all %s)", _PERSISTENCE_PEN, last_n)

        # Step 9 — Suppression penalty: masked distress is still distress
        if suppression_flagged and raw_mhi > 50.0:
            raw_mhi = max(0.0, raw_mhi - 8.0)
            logger.debug("Suppression penalty: -8 pts")

        # Step 10 — Emotion complexity penalty: mixed emotions signal hidden distress
        if emotion_complexity > 0.15 and emotion_label != "neutral":
            complexity_pen = min(emotion_complexity * 12.0, 6.0)
            raw_mhi = max(0.0, raw_mhi - complexity_pen)
            logger.debug("Complexity penalty: %.1f pts (complexity=%.3f)", complexity_pen, emotion_complexity)

        # Step 11 — Positive indicators bonus (only when not in crisis tier)
        if crisis_tier == "none" and raw_text:
            pos_matches = len(_POSITIVE_INDICATORS.findall(raw_text))
            if pos_matches > 0:
                bonus = min(_POSITIVE_BASE_BONUS + (pos_matches - 1) * 1.5, _POSITIVE_MAX_BONUS)
                raw_mhi = min(100.0, raw_mhi + bonus)
                logger.debug("Positive indicator bonus: +%.1f pts (%d matches)", bonus, pos_matches)

        # Step 12 — Linguistic complexity / engagement bonus
        if raw_text and crisis_tier == "none":
            word_count = len(raw_text.split())
            if word_count >= _MIN_WORDS_FOR_COMPLEXITY:
                raw_mhi = min(100.0, raw_mhi + _COMPLEXITY_BONUS)

        # Step 13 — Hard ceiling by crisis tier
        ceiling = _CRISIS_CEIL.get(crisis_tier, 100.0)
        final   = round(min(raw_mhi, ceiling), 2)

        logger.debug(
            "MHI | E=%.2f(%s) C=%.2f(%s) B=%.2f S=%.2f H=%.2f(adj=%.2f) "
            "→ raw=%.1f hop=%.0f → final=%.1f [ceil=%.0f]",
            emotion_score, emotion_label, crisis_score, crisis_tier,
            behavioral_score, screening_score, history_score, adjusted_history,
            raw_mhi + hop_pen, hop_pen, final, ceiling,
        )
        return final

    def categorize(
        self,
        mhi:          float,
        crisis_score: float,
        crisis_tier:  str = "none",
    ) -> str:
        """
        7-band risk category from MHI + crisis signals.
        Hard overrides for active/passive crisis tiers take absolute priority.
        """
        # Hard overrides
        if crisis_tier == "active"  or crisis_score >= 0.85:
            return "Crisis Risk"
        if crisis_tier == "passive" or crisis_score >= settings.CRISIS_PROBABILITY_THRESHOLD:
            return "Severe Risk"

        # 7-band MHI categorization (descending threshold check)
        for threshold, label in _MHI_BANDS:
            if mhi >= threshold:
                return label

        return "Crisis Risk"

    # ── Internal helpers

    @staticmethod
    def _trend_history(
        history_score: float,
        mhi_trend:     list[float] | None,
    ) -> float:
        """
        Amplifies history_score if the user's MHI trend is worsening.

        mhi_trend : list of recent MHI values, oldest first.
        Returns   : adjusted history_score ∈ [0, 1]

        Rules:
          - Monotonically declining last 3 values  → multiply by 1.4
          - Average of last 3 below 50             → multiply by 1.2
          - Otherwise                              → unchanged
        """
        if not mhi_trend or len(mhi_trend) < 2:
            return history_score

        recent = mhi_trend[-3:]

        # Declining trend (each value worse than previous)
        if all(recent[i] > recent[i+1] for i in range(len(recent)-1)):
            return min(history_score * 1.4, 1.0)

        # Persistently low average
        if (sum(recent) / len(recent)) < 50.0:
            return min(history_score * 1.2, 1.0)

        return history_score
