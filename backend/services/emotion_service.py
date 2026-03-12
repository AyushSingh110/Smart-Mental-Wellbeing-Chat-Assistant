from __future__ import annotations

import logging
import os
import re
import torch
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification

logger = logging.getLogger(__name__)

_LOCAL_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "models", "emotion")
)

# ── Canonical labels used everywhere in the pipeline
CANONICAL_LABELS = ["stress", "anxiety", "sadness", "anger", "fear", "neutral"]

# Any label the fine-tuned model might output  = canonical label 
_LABEL_MAP: dict[str, str] = {
    "stress":     "stress",
    "anxiety":    "anxiety",  "anxious":   "anxiety",
    "sadness":    "sadness",  "sad":       "sadness",
    "depression": "sadness",  "depressed": "sadness",   "grief":    "sadness",
    "anger":      "anger",    "angry":     "anger",     "disgust":  "anger",
    "fear":       "fear",     "scared":    "fear",      "panic":    "fear",
    "neutral":    "neutral",
    # positive → neutral (no clinical risk)
    "joy":        "neutral",  "happy":     "neutral",
    "love":       "neutral",  "surprise":  "neutral",   "happiness":"neutral",
    # numeric LABEL_N fallbacks
    "label_0":    "sadness",  "label_1":   "neutral",
    "label_2":    "anger",    "label_3":   "fear",
    "label_4":    "neutral",  "label_5":   "surprise",
}

_KEYWORD_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(sad|cry|depress|grief|loss|heartbreak)\b", re.I), "sadness"),
    (re.compile(r"\b(anxious|anxiety|worry|worri|nervous|panic)\b", re.I), "anxiety"),
    (re.compile(r"\b(stress|overwhelm|exhaust|burnout|pressure)\b", re.I), "stress"),
    (re.compile(r"\b(afraid|scare|fear|terrif|dread)\b", re.I), "fear"),
    (re.compile(r"\b(angry|anger|furious|rage|hate|frustrat)\b", re.I), "anger"),
]


class EmotionService:

    def __init__(self):
        self.tokenizer = None
        self.model     = None
        self._loaded   = False
        self._load()

    # Loading
    def _load(self) -> None:
        path = os.getenv("EMOTION_MODEL_PATH", "").strip() or _LOCAL_PATH
        try:
            self.tokenizer = DistilBertTokenizerFast.from_pretrained(path)
            self.model     = DistilBertForSequenceClassification.from_pretrained(path)
            self.model.eval()
            self._loaded   = True
            logger.info(
                "EmotionService | loaded from: %s | model labels: %s",
                path, list(self.model.config.id2label.values()),
            )
        except Exception as exc:
            logger.error(
                "EmotionService | failed to load from %s: %s — using keyword fallback",
                path, exc,
            )
            self._loaded = False

    # Public API

    def predict(self, text: str) -> dict[str, float]:
        """
        Returns canonical emotion score dict.
        All 6 labels always present, values sum to 1.0.
        """
        if self._loaded:
            try:
                return self._model_predict(text)
            except Exception as exc:
                logger.error("EmotionService.predict runtime error: %s", exc)
        return self._keyword_fallback(text)

    #  Internals
    def _model_predict(self, text: str) -> dict[str, float]:
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
        scores: dict[str, float] = {lbl: 0.0 for lbl in CANONICAL_LABELS}

        for idx, prob in enumerate(probs.tolist()):
            raw    = id2label.get(idx, f"label_{idx}").lower()
            canon  = _LABEL_MAP.get(raw, "neutral")
            scores[canon] = scores[canon] + prob

        total = sum(scores.values()) or 1.0
        return {k: round(v / total, 4) for k, v in scores.items()}

    @staticmethod
    def _keyword_fallback(text: str) -> dict[str, float]:
        scores = {lbl: 0.04 for lbl in CANONICAL_LABELS}
        for pattern, label in _KEYWORD_RULES:
            if pattern.search(text):
                scores[label] += 0.55
        total = sum(scores.values()) or 1.0
        return {k: round(v / total, 4) for k, v in scores.items()}
