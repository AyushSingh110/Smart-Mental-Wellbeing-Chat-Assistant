from __future__ import annotations

import logging
import os
import re
import torch
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification

logger = logging.getLogger(__name__)

# ── Model path ────────────────────────────────────────────────────────────────
_LOCAL_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "models", "crisis")
)

# ── Active suicidal intent patterns — hard floor 0.90 ────────────────────────
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

# ── Passive death-wish patterns — hard floor 0.60 ─────────────────────────────
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

# ── Distress signals — no hard floor, model + rule max ───────────────────────
_DISTRESS: list[tuple[re.Pattern, float]] = [
    (re.compile(r"\b(no\s+hope|hopeless|feel\s+empty)\b",           re.I), 0.44),
    (re.compile(r"\b(so\s+much\s+pain|can'?t\s+take\s+the\s+pain)\b", re.I), 0.46),
    (re.compile(r"\b(feel\s+like\s+giving\s+up)\b",                 re.I), 0.48),
    (re.compile(r"\b(falling\s+apart|breaking\s+down)\b",           re.I), 0.40),
    (re.compile(r"\b(completely\s+(lost|alone|isolated))\b",        re.I), 0.38),
]

# Tier severity order (higher index = more severe)
_TIER_ORDER = {"none": 0, "distress": 1, "passive": 2, "active": 3}


class CrisisService:

    def __init__(self):
        self.tokenizer = None
        self.model     = None
        self._loaded   = False
        self._load()

    # ── Loading ───────────────────────────────────────────────────────────────

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

    # ── Public API ────────────────────────────────────────────────────────────

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
        return tier

    # ── Internals ─────────────────────────────────────────────────────────────

    def _rule_score(self, text: str) -> tuple[float, str]:
        """Returns (score, tier) for the highest-severity rule match."""
        lowered = text.lower()

        for pattern, score in _ACTIVE:
            if pattern.search(lowered):
                return score, "active"

        for pattern, score in _PASSIVE:
            if pattern.search(lowered):
                return score, "passive"

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
                # Accept any label that clearly signals crisis
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
