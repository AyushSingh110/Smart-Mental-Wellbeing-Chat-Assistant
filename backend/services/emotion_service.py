from __future__ import annotations

import os
import re
import logging
import statistics
from dataclasses import dataclass, field
from typing import Optional

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

# ── Hedging patterns: "I think I'm fine", "maybe it's nothing", "probably okay"
_HEDGING_RE = re.compile(
    r"\b("
    r"i\s+(think|guess|suppose|believe)\s+(i'?m\s+)?(fine|okay|ok|alright|good|not\s+that\s+bad)|"
    r"(maybe|perhaps|probably|might\s+be)\s+(it'?s?\s+)?(nothing|fine|okay|ok|just\s+stress)|"
    r"(not\s+sure\s+if|don'?t\s+know\s+if)\s+it'?s?\s+that\s+(bad|serious|big)|"
    r"(just|only)\s+(a\s+bit|a\s+little|slightly)\s+(sad|anxious|stressed|worried)|"
    r"(shouldn'?t\s+complain|others\s+have\s+it\s+worse|i'?ll\s+be\s+fine|i\s+can\s+handle\s+it)|"
    r"(no\s+biggie|nothing\s+major|don'?t\s+mind\s+me)|"
    r"(i\s+don'?t\s+want\s+to\s+(bother|burden|worry)\s+(you|anyone))"
    r")\b",
    re.I,
)

# ── Masking/suppression patterns: forced positivity over distress
_MASKING_RE = re.compile(
    r"\b("
    r"(pretend(ing)?|act(ing)?\s+like)\s+(everything('?s)?\s+(fine|okay|normal)|i'?m\s+(fine|okay|happy))|"
    r"(wear(ing)?\s+a\s+(smile|mask)|put\s+on\s+a\s+(brave\s+face|front))|"
    r"(smile\s+(through|despite)|laugh\s+(it\s+off|through\s+the\s+pain))|"
    r"(nobody\s+knows|hide\s+it|keep\s+it\s+(inside|to\s+myself|hidden))|"
    r"(on\s+the\s+outside\s+i'?m?\s+(fine|okay|happy)|inside\s+i'?m?\s+(not|hurting|broken|empty))|"
    r"(fake\s+(smile|laugh|it)|force\s+(a\s+)?(smile|laugh))|"
    r"(told\s+everyone\s+(i'?m\s+)?(fine|okay)|acting\s+normal\s+but)"
    r")\b",
    re.I,
)


@dataclass
class EmotionFullResult:
    """Rich emotion analysis result returned by predict_full()."""
    scores: dict[str, float]                    # canonical emotion scores, sum ≈ 1.0
    top_label: str                               # highest-confidence canonical label
    top_score: float                             # confidence of top label
    top_3: list[tuple[str, float]]              # top-3 (label, score) sorted descending
    emotion_complexity: float                   # std-dev of top-3 scores (0=pure, 1=mixed)
    suppression_flagged: bool                   # masking pattern detected
    hedging_detected: bool                      # hedging/minimisation pattern detected


class EmotionService:

    def __init__(self):
        self.tokenizer = None
        self.model     = None
        self._loaded   = False
        self._load()

    # ── Loading
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

    # ── Public API

    def predict(self, text: str) -> dict[str, float]:
        """
        Backward-compatible API.
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

    def predict_full(self, text: str) -> EmotionFullResult:
        """
        Extended analysis returning:
        - Full score dict
        - Top-3 (label, score) tuples
        - emotion_complexity (std-dev of top-3 scores)
        - suppression_flagged (masking/suppression patterns)
        - hedging_detected (minimisation language)
        """
        scores = self.predict(text)

        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_3 = sorted_scores[:3]
        top_label, top_score = sorted_scores[0]

        # emotion_complexity: std-dev of top-3 confidence values
        # Low value = one dominant emotion (pure); high = mixed/ambiguous
        top_3_values = [s for _, s in top_3]
        try:
            emotion_complexity = round(statistics.stdev(top_3_values), 4) if len(top_3_values) >= 2 else 0.0
        except statistics.StatisticsError:
            emotion_complexity = 0.0

        # Detect suppression/masking
        suppression_flagged = bool(_MASKING_RE.search(text))

        # Detect hedging/minimisation
        hedging_detected = bool(_HEDGING_RE.search(text))

        # If hedging detected with a non-neutral top emotion, slightly reduce top confidence
        # (signal that the user is downplaying their state)
        if hedging_detected and top_label != "neutral" and top_score > 0.40:
            adjusted_scores = dict(scores)
            shift = min(0.12, top_score * 0.18)
            adjusted_scores[top_label] = round(max(0.0, top_score - shift), 4)
            adjusted_scores["neutral"] = round(adjusted_scores.get("neutral", 0.0) + shift * 0.5, 4)
            total = sum(adjusted_scores.values()) or 1.0
            adjusted_scores = {k: round(v / total, 4) for k, v in adjusted_scores.items()}
            sorted_scores = sorted(adjusted_scores.items(), key=lambda x: x[1], reverse=True)
            top_3 = sorted_scores[:3]
            top_label, top_score = sorted_scores[0]
            scores = adjusted_scores

        logger.debug(
            "EmotionFull | top=%s(%.2f) complexity=%.3f suppress=%s hedge=%s",
            top_label, top_score, emotion_complexity, suppression_flagged, hedging_detected,
        )

        return EmotionFullResult(
            scores=scores,
            top_label=top_label,
            top_score=top_score,
            top_3=top_3,
            emotion_complexity=emotion_complexity,
            suppression_flagged=suppression_flagged,
            hedging_detected=hedging_detected,
        )

    # ── Internals
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
