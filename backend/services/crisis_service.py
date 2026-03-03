from __future__ import annotations

import re
import torch
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification

# ── Tier 1: Active suicidal intent — hard floor at 0.90 ───────────────────────
_ACTIVE_INTENT_PATTERNS: list[tuple[str, float]] = [
    (r"\b(kill\s+myself|killing\s+myself)\b", 0.97),
    (r"\b(end\s+my\s+life|ending\s+my\s+life)\b", 0.95),
    (r"\b(want\s+to\s+die|want\s+to\s+be\s+dead)\b", 0.93),
    (r"\b(going\s+to\s+(kill|hurt)\s+myself)\b", 0.96),
    (r"\b(suicide\s+plan|planned\s+to\s+die)\b", 0.97),
    (r"\b(no\s+reason\s+to\s+(live|be\s+alive))\b", 0.90),
    (r"\b(better\s+off\s+dead|better\s+if\s+i\s+(died|was\s+gone))\b", 0.88),
    (r"\b(take\s+my\s+own\s+life)\b", 0.96),
]

# ── Tier 2: Passive death wish — hard floor at 0.60 ───────────────────────────
_PASSIVE_WISH_PATTERNS: list[tuple[str, float]] = [
    (r"\b(wish\s+(i\s+was|i\s+were)\s+dead)\b", 0.75),
    (r"\b(don'?t\s+want\s+to\s+(be\s+here|exist|wake\s+up))\b", 0.72),
    (r"\b(wish\s+(everything|it\s+all)\s+would\s+end)\b", 0.70),
    (r"\b(want\s+to\s+disappear|just\s+disappear)\b", 0.65),
    (r"\b(everything\s+would\s+be\s+easier\s+if\s+i\s+(was|were)\s+(gone|dead))\b", 0.78),
    (r"\b(easier\s+if\s+i\s+(just\s+)?(disappeared|was\s+gone|wasnt\s+here))\b", 0.76),
    (r"\b(tired\s+of\s+(living|being\s+alive|existing))\b", 0.68),
    (r"\b(can'?t\s+(do\s+this|keep\s+going|go\s+on)\s+anymore)\b", 0.62),
    (r"\b(want\s+to\s+end\s+(all|everything|it(\s+all)?))\b", 0.70),
    (r"\b(end\s+all\s+the\s+(things|pain|suffering))\b", 0.68),
    (r"\b(pointless\s+to\s+(live|keep\s+going|continue))\b", 0.68),
    (r"\b(feel\s+like\s+(dying|i\s+am\s+dying))\b", 0.72),
]

# ── Tier 3: Distress signals — no floor, model + rule max ─────────────────────
_DISTRESS_PATTERNS: list[tuple[str, float]] = [
    (r"\b(no\s+hope|hopeless|feel\s+empty)\b", 0.42),
    (r"\b(nobody\s+(cares|would\s+miss\s+me))\b", 0.50),
    (r"\b(burden\s+to\s+(everyone|others|my\s+family))\b", 0.52),
    (r"\b(so\s+much\s+pain|can'?t\s+take\s+the\s+pain)\b", 0.45),
    (r"\b(feel\s+like\s+giving\s+up)\b", 0.48),
    (r"\b(don'?t\s+have\s+the\s+energy\s+to\s+keep\s+going)\b", 0.44),
]

MODEL_PATH = "models/crisis_distilbert"


class CrisisService:

    def __init__(self):
        try:
            self.tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_PATH)
            self.model = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH)
        except Exception:
            # Fallback to base model if fine-tuned weights unavailable
            self.tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
            self.model = DistilBertForSequenceClassification.from_pretrained(
                "distilbert-base-uncased", num_labels=2
            )
        self.model.eval()

    def _rule_score(self, text: str) -> tuple[float, str]:
        lowered = text.lower()
        for pattern, score in _ACTIVE_INTENT_PATTERNS:
            if re.search(pattern, lowered):
                return score, "active"
        for pattern, score in _PASSIVE_WISH_PATTERNS:
            if re.search(pattern, lowered):
                return score, "passive"
        for pattern, score in _DISTRESS_PATTERNS:
            if re.search(pattern, lowered):
                return score, "distress"
        return 0.0, "none"

    def _model_score(self, text: str) -> float:
        inputs = self.tokenizer(
            text, return_tensors="pt", truncation=True, padding=True, max_length=128
        )
        with torch.no_grad():
            probs = torch.softmax(self.model(**inputs).logits, dim=1)
        return probs[0][1].item()

    def predict(self, text: str) -> float:
        rule_score, tier = self._rule_score(text)
        model_score = self._model_score(text)

        if tier == "active":
            return max(rule_score, model_score, 0.90)
        if tier == "passive":
            return max(0.65 * rule_score + 0.35 * model_score, 0.60)
        if tier == "distress":
            return max(rule_score, model_score)
        return model_score

    def classify_tier(self, text: str) -> str:
        """Returns 'active' | 'passive' | 'distress' | 'none'"""
        _, tier = self._rule_score(text)
        return tier