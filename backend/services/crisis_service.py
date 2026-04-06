from __future__ import annotations

import os
import re
import logging
from collections import deque
from typing import Optional

import torch
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification

from backend.config import settings

logger = logging.getLogger(__name__)

# Model path
_LOCAL_PATH = os.path.abspath(settings.CRISIS_MODEL_PATH)

# ── Active suicidal intent patterns — hard floor 0.90
_ACTIVE: list[tuple[re.Pattern, float]] = [
    (re.compile(r"\b(kill\s+myself|killing\s+myself)\b",                        re.I), 0.97),
    (re.compile(r"\b(end\s+my\s+life|ending\s+my\s+life)\b",                   re.I), 0.95),
    (re.compile(r"\b(want\s+to\s+die|want\s+to\s+be\s+dead)\b",                re.I), 0.93),
    (re.compile(r"\b(going\s+to\s+(kill|hurt)\s+myself)\b",                    re.I), 0.96),
    (re.compile(r"\b(suicide\s+plan|planned?\s+to\s+die)\b",                   re.I), 0.97),
    (re.compile(r"\b(no\s+reason\s+to\s+(live|be\s+alive))\b",                 re.I), 0.90),
    (re.compile(r"\b(better\s+off\s+dead|better\s+if\s+i\s+(died|was\s+gone))\b", re.I), 0.88),
    (re.compile(r"\b(take\s+my\s+own\s+life)\b",                               re.I), 0.96),
    (re.compile(r"\b(self[\s\-]harm|cut\s+myself|overdose\s+on)\b",            re.I), 0.91),
]

# ── Passive death-wish patterns — hard floor 0.60
_PASSIVE: list[tuple[re.Pattern, float]] = [
    (re.compile(r"\b(wish\s+(i\s+was|i\s+were)\s+dead)\b",                     re.I), 0.78),
    (re.compile(r"\b(don'?t\s+want\s+to\s+(be\s+here|exist|wake\s+up))\b",     re.I), 0.74),
    (re.compile(r"\bwant\s+to\s+disappear\b",                                  re.I), 0.68),
    (re.compile(r"\bjust\s+disappear\b",                                        re.I), 0.66),
    (re.compile(r"\b(easier\s+if\s+i\s+(just\s+)?(disappeared|was\s+gone|wasnt?\s+here))\b", re.I), 0.78),
    (re.compile(r"\beverything\s+would\s+be\s+easier\s+if\s+i\s+(was|were)\s+(gone|dead)\b", re.I), 0.80),
    (re.compile(r"\b(tired\s+of\s+(living|being\s+alive|existing))\b",         re.I), 0.70),
    (re.compile(r"\b(can'?t\s+(do\s+this|keep\s+going|go\s+on)\s+anymore)\b",  re.I), 0.65),
    (re.compile(r"\b(want\s+to\s+end\s+(all|everything|it(\s+all)?))\b",       re.I), 0.72),
    (re.compile(r"\b(pointless\s+to\s+(live|keep\s+going))\b",                 re.I), 0.68),
    (re.compile(r"\b(feel\s+like\s+(dying|i\s+am\s+dying))\b",                 re.I), 0.74),
    (re.compile(r"\b(wish\s+(everything|it\s+all)\s+would\s+end)\b",           re.I), 0.72),
    (re.compile(r"\b(nobody\s+(cares|would\s+miss\s+me))\b",                   re.I), 0.62),
    (re.compile(r"\b(burden\s+to\s+(everyone|others|my\s+family))\b",          re.I), 0.64),
]

# ── Distress signals — no hard floor, model + rule max
_DISTRESS: list[tuple[re.Pattern, float]] = [
    (re.compile(r"\b(no\s+hope|hopeless|feel\s+empty)\b",           re.I), 0.44),
    (re.compile(r"\b(so\s+much\s+pain|can'?t\s+take\s+the\s+pain)\b", re.I), 0.46),
    (re.compile(r"\b(feel\s+like\s+giving\s+up)\b",                 re.I), 0.48),
    (re.compile(r"\b(falling\s+apart|breaking\s+down)\b",           re.I), 0.40),
    (re.compile(r"\b(completely\s+(lost|alone|isolated))\b",        re.I), 0.38),
]

# ── Indian cultural crisis phrases (25 phrases across 4 groups)
# Group 1: Hindi/Hinglish suicidal ideation
_INDIAN_ACTIVE: list[tuple[re.Pattern, float]] = [
    (re.compile(r"\b(khatam\s+karna\s+chahta|khatam\s+ho\s+jana\s+chahta)\b",  re.I), 0.92),
    (re.compile(r"\b(zindagi\s+se\s+(tang|pareshaan)\s+aa\s+gaya)\b",          re.I), 0.88),
    (re.compile(r"\b(marna\s+chahta|mar\s+jana\s+chahta)\b",                   re.I), 0.94),
    (re.compile(r"\b(khatam\s+kar\s+loon\s+sab\s+kuch)\b",                     re.I), 0.91),
    (re.compile(r"\b(jaan\s+de\s+doon|jaan\s+dene\s+ka\s+mann)\b",            re.I), 0.95),
]

# Group 2: Hindi/Hinglish passive ideation
_INDIAN_PASSIVE: list[tuple[re.Pattern, float]] = [
    (re.compile(r"\b(gaayab\s+ho\s+jana\s+chahta|gaayab\s+ho\s+jaata)\b",      re.I), 0.70),
    (re.compile(r"\b(sab\s+(chhod|chodh)\s+dena\s+chahta)\b",                  re.I), 0.66),
    (re.compile(r"\b(thak\s+gaya\s+(hoon|hu)\s+(jeene\s+se|sab\s+se))\b",     re.I), 0.72),
    (re.compile(r"\b(koi\s+nahi\s+chahta\s+mujhe|koi\s+nahi\s+hai\s+mera)\b", re.I), 0.64),
    (re.compile(r"\b(iss\s+duniya\s+mein\s+nahi\s+rehna|yahan\s+se\s+chale\s+jaana)\b", re.I), 0.76),
    (re.compile(r"\b(boj\s+ban\s+gaya\s+(hoon|hu)|sabke\s+liye\s+boj)\b",     re.I), 0.68),
]

# Group 3: Tamil/Telugu/Kannada/Malayalam common distress phrases (transliterated)
_INDIAN_REGIONAL: list[tuple[re.Pattern, float]] = [
    (re.compile(r"\b(vaazhve\s+vendam|vaazhkkai\s+vendam)\b",                  re.I), 0.88),   # Tamil: don't want life
    (re.compile(r"\b(saaka\s+manasundi|saavaalani\s+undi)\b",                  re.I), 0.91),   # Telugu: want to die
    (re.compile(r"\b(saaybekku\s+anisatte|badukuvudu\s+beda)\b",               re.I), 0.89),   # Kannada: want to die
    (re.compile(r"\b(jeevikkan\s+thaalparyam\s+illa|marikkanam\s+ennu)\b",     re.I), 0.90),   # Malayalam: don't want to live
    (re.compile(r"\b(maranam\s+vendum|uruppadi\s+vaazha\s+mudiyalai)\b",       re.I), 0.87),   # Tamil: want death
    (re.compile(r"\b(praanalu\s+teesukovalani|chaavaalani\s+anipistundi)\b",   re.I), 0.92),   # Telugu: want to take life
]

# Group 4: Mixed / code-switching expressions common in urban India
_INDIAN_CODEMIX: list[tuple[re.Pattern, float]] = [
    (re.compile(r"\b(i\s+am\s+so\s+done\s+yaar|done\s+ho\s+gaya\s+hoon)\b",   re.I), 0.58),
    (re.compile(r"\b(sab\s+kuch\s+end\s+karna\s+chahta\s+(hoon|hu))\b",       re.I), 0.88),
    (re.compile(r"\b(life\s+mein\s+kuch\s+nahi\s+(bacha|raha))\b",            re.I), 0.62),
    (re.compile(r"\b(ab\s+nahi\s+rehna|aur\s+nahi\s+jina)\b",                 re.I), 0.78),
]

# ── Tier severity order (higher index = more severe)
_TIER_ORDER = {"none": 0, "distress": 1, "passive": 2, "active": 3}

# ── Temporal escalation settings
_ESCALATION_WINDOW = 3        # consecutive turns above threshold → escalate
_ESCALATION_THRESHOLD = 0.40  # crisis_score threshold per turn


class CrisisService:

    def __init__(self):
        self.tokenizer = None
        self.model     = None
        self._loaded   = False
        # Per-user crisis history for temporal escalation
        # key: user_id (str), value: deque of (crisis_score, tier) tuples
        self._crisis_history: dict[str, deque] = {}
        self._load()

    # ── Loading

    def _load(self) -> None:
        path = os.getenv("CRISIS_MODEL_PATH", "").strip() or _LOCAL_PATH
        try:
            self.tokenizer = DistilBertTokenizerFast.from_pretrained(path)
            self.model     = DistilBertForSequenceClassification.from_pretrained(path)
            self.model.eval()
            self._loaded   = True
            logger.info(
                "CrisisService | loaded from: %s | labels: %s",
                path, list(self.model.config.id2label.values()),
            )
        except Exception as exc:
            logger.error(
                "CrisisService | failed to load from %s: %s — using regex-only mode",
                path, exc,
            )
            self._loaded = False

    # ── Public API

    def predict(self, text: str) -> float:
        """
        Returns crisis probability in [0.0, 1.0].
        Rules set hard floors so obvious language is never under-scored.
        """
        rule_score, tier = self._rule_score(text)
        model_score      = self._model_score(text)

        if tier == "active":
            return round(max(rule_score, model_score, 0.90), 4)
        if tier == "passive":
            return round(max(0.65 * rule_score + 0.35 * model_score, 0.60), 4)
        if tier == "distress":
            return round(max(rule_score, model_score), 4)
        return round(model_score, 4)

    def classify_tier(self, text: str) -> str:
        """Returns 'active' | 'passive' | 'distress' | 'none'"""
        _, tier = self._rule_score(text)
        if tier != "none":
            return tier

        model_score = self._model_score(text)
        if model_score >= settings.SAFETY_OVERRIDE_THRESHOLD:
            return "active"
        if model_score >= settings.CRISIS_PROBABILITY_THRESHOLD:
            return "passive"
        if model_score >= 0.30:
            return "distress"
        return "none"

    def classify_tier_with_history(self, text: str, user_id: str) -> tuple[str, float]:
        """
        Like classify_tier() but also considers temporal escalation.
        Returns (tier, crisis_score).

        Temporal escalation rule:
          If the last N consecutive turns all have crisis_score > threshold,
          the tier is escalated to at least "passive" even if current tier is "distress".
        """
        score = self.predict(text)
        tier  = self.classify_tier(text)

        # Update per-user history
        if user_id not in self._crisis_history:
            self._crisis_history[user_id] = deque(maxlen=_ESCALATION_WINDOW + 2)
        self._crisis_history[user_id].append((score, tier))

        # Temporal escalation: if last N turns all above threshold
        history = list(self._crisis_history[user_id])
        if len(history) >= _ESCALATION_WINDOW:
            recent = history[-_ESCALATION_WINDOW:]
            all_elevated = all(s > _ESCALATION_THRESHOLD for s, _ in recent)
            if all_elevated and _TIER_ORDER.get(tier, 0) < _TIER_ORDER["passive"]:
                logger.info(
                    "CrisisService | temporal escalation → passive (user=%s, last %d turns all >%.2f)",
                    user_id, _ESCALATION_WINDOW, _ESCALATION_THRESHOLD,
                )
                tier = "passive"

        return tier, score

    def get_crisis_velocity(self, user_id: str) -> float:
        """
        Returns the rate of change of crisis_score across the last few turns.
        Positive = escalating, Negative = de-escalating, 0 = stable.

        Value is in the range approximately [-1.0, 1.0].
        """
        history = list(self._crisis_history.get(user_id, deque()))
        if len(history) < 2:
            return 0.0

        scores = [s for s, _ in history[-4:]]  # up to last 4 turns
        if len(scores) < 2:
            return 0.0

        # Linear slope estimate: (last - first) / window
        velocity = (scores[-1] - scores[0]) / (len(scores) - 1)
        return round(max(-1.0, min(1.0, velocity)), 4)

    def reset_user_history(self, user_id: str) -> None:
        """Clear temporal history for a user (e.g. on logout)."""
        self._crisis_history.pop(user_id, None)

    # ── Internals

    def _rule_score(self, text: str) -> tuple[float, str]:
        """Returns (score, tier) for the highest-severity rule match."""
        lowered = text.lower()

        # Check English active patterns
        for pattern, score in _ACTIVE:
            if pattern.search(lowered):
                return score, "active"

        # Check Indian-language active patterns
        for pattern, score in _INDIAN_ACTIVE:
            if pattern.search(lowered):
                return score, "active"

        # Check Indian-language regional patterns (often active-level)
        for pattern, score in _INDIAN_REGIONAL:
            if pattern.search(lowered):
                tier = "active" if score >= 0.85 else "passive"
                return score, tier

        # Check English passive patterns
        for pattern, score in _PASSIVE:
            if pattern.search(lowered):
                return score, "passive"

        # Check Indian-language passive patterns
        for pattern, score in _INDIAN_PASSIVE:
            if pattern.search(lowered):
                return score, "passive"

        # Check code-mix patterns
        for pattern, score in _INDIAN_CODEMIX:
            if pattern.search(lowered):
                tier = "active" if score >= 0.75 else ("passive" if score >= 0.55 else "distress")
                return score, tier

        # Check distress signals
        for pattern, score in _DISTRESS:
            if pattern.search(lowered):
                return score, "distress"

        return 0.0, "none"

    def _model_score(self, text: str) -> float:
        """
        Returns the model's crisis probability.
        Handles both binary (crisis/no_crisis) and multi-class outputs.
        Falls back to 0.0 if model is unavailable.
        """
        if not self._loaded:
            return 0.0
        try:
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=128,
            )
            with torch.no_grad():
                probs = torch.softmax(
                    self.model(**inputs).logits, dim=1
                ).squeeze()

            id2label = self.model.config.id2label
            crisis_score = 0.0

            for idx, prob in enumerate(probs.tolist()):
                label = id2label.get(idx, "").lower()
                if any(kw in label for kw in
                       ("crisis", "active", "suicide", "harm", "label_1")):
                    crisis_score = max(crisis_score, prob)

            # If model uses plain LABEL_0 / LABEL_1 binary, take index-1 as crisis
            if crisis_score == 0.0 and len(probs) == 2:
                crisis_score = probs[1].item()

            return round(crisis_score, 4)

        except Exception as exc:
            logger.error("CrisisService._model_score error: %s", exc)
            return 0.0
