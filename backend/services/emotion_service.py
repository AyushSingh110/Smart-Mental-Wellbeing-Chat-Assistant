from __future__ import annotations

import os
import re
import logging

import torch
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification

from backend.config import settings

logger = logging.getLogger(__name__)

_LOCAL_PATH = settings.EMOTION_MODEL_PATH

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
    "label_4":    "neutral",  "label_5":   "neutral",
}

_KEYWORD_RULES: list[tuple[re.Pattern, str, float]] = [
    (re.compile(r"\b(sad|cry(ing)?|depress(ed|ing)?|grief|loss|heartbreak|empty|numb|lonely|disappear)\b", re.I), "sadness", 0.46),
    (re.compile(r"\b(anxious|anxiety|worr(y|ied|ying)|nervous|panic(king)?|restless|racing\s+thoughts?)\b", re.I), "anxiety", 0.48),
    (re.compile(r"\b(stress(ed|ful)?|overwhelm(ed|ing)?|exhaust(ed|ing)?|burnout|pressure|drained|too\s+much)\b", re.I), "stress", 0.46),
    (re.compile(r"\b(afraid|scared|fear(ful)?|terrif(ied|ying)?|dread|unsafe)\b", re.I), "fear", 0.50),
    (re.compile(r"\b(angry|anger|furious|rage|hate|frustrat(ed|ing)?|irritat(ed|ing)?)\b", re.I), "anger", 0.42),
]

_INTENSIFIERS = re.compile(
    r"\b(very|really|extremely|so|too|super|deeply|completely|totally|constantly)\b",
    re.I,
)
_NEGATIONS = re.compile(r"\b(not|never|hardly|barely|don't|cant|can't|isn't|wasn't)\b", re.I)
_QUESTION_RE = re.compile(r"\?$")
_HOPELESS_EMOTION = re.compile(r"\b(disappear|gone|dead|empty|numb|hopeless|pointless)\b", re.I)


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
        keyword_scores = self._keyword_scores(text)
        if self._loaded:
            try:
                return self._blend_scores(self._model_predict(text), keyword_scores, text)
            except Exception as exc:
                logger.error("EmotionService.predict runtime error: %s", exc)
        return keyword_scores

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
    def _keyword_scores(text: str) -> dict[str, float]:
        lowered = text.strip().lower()
        scores = {lbl: 0.03 for lbl in CANONICAL_LABELS}

        for pattern, label, weight in _KEYWORD_RULES:
            matches = len(pattern.findall(lowered))
            if matches:
                scores[label] += min(weight + (matches - 1) * 0.08, 0.68)

        if _INTENSIFIERS.search(lowered):
            top_label = max(scores, key=scores.get)
            if top_label != "neutral":
                scores[top_label] += 0.08

        if _QUESTION_RE.search(lowered) and any(token in lowered for token in ("what if", "am i", "will i", "should i")):
            scores["anxiety"] += 0.10

        if _NEGATIONS.search(lowered) and scores["anger"] > 0.03:
            scores["anger"] = max(0.03, scores["anger"] - 0.06)
            scores["stress"] += 0.04

        if max(scores.values()) <= 0.11:
            scores["neutral"] += 0.62

        total = sum(scores.values()) or 1.0
        return {k: round(v / total, 4) for k, v in scores.items()}

    @staticmethod
    def _blend_scores(
        model_scores: dict[str, float],
        keyword_scores: dict[str, float],
        text: str,
    ) -> dict[str, float]:
        keyword_top = max(keyword_scores, key=keyword_scores.get)
        use_keyword_heavier = keyword_top != "neutral" and keyword_scores[keyword_top] >= 0.28
        model_weight = 0.45 if use_keyword_heavier else 0.72
        keyword_weight = 0.55 if use_keyword_heavier else 0.28

        blended = {
            label: model_weight * model_scores.get(label, 0.0) + keyword_weight * keyword_scores.get(label, 0.0)
            for label in CANONICAL_LABELS
        }

        if len(text.split()) <= 3 and max(blended.values()) < 0.45:
            blended["neutral"] += 0.20

        total = sum(blended.values()) or 1.0
        normalized = {k: round(v / total, 4) for k, v in blended.items()}

        top_label = max(normalized, key=normalized.get)
        if keyword_top != "neutral" and keyword_scores[keyword_top] >= 0.34 and (
            normalized[top_label] < 0.42 or top_label == "neutral"
        ):
            normalized[keyword_top] = round(normalized[keyword_top] + 0.28, 4)
            normalized["neutral"] = max(0.01, round(normalized["neutral"] - 0.14, 4))
            total = sum(normalized.values()) or 1.0
            normalized = {k: round(v / total, 4) for k, v in normalized.items()}
            top_label = max(normalized, key=normalized.get)

        if top_label != "neutral" and normalized[top_label] < 0.34:
            normalized["neutral"] = round(normalized["neutral"] + 0.18, 4)
            total = sum(normalized.values()) or 1.0
            normalized = {k: round(v / total, 4) for k, v in normalized.items()}

        if _HOPELESS_EMOTION.search(text) and normalized["sadness"] >= 0.18 and normalized["anger"] > normalized["sadness"]:
            shift = min(0.16, normalized["anger"] - normalized["sadness"] + 0.02)
            normalized["anger"] = round(max(0.01, normalized["anger"] - shift), 4)
            normalized["sadness"] = round(normalized["sadness"] + shift, 4)
            total = sum(normalized.values()) or 1.0
            normalized = {k: round(v / total, 4) for k, v in normalized.items()}

        return normalized
