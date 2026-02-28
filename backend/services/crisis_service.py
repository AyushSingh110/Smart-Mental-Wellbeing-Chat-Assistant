"""
Crisis detection service – multi‑layer approach:

1. Rule‑based keyword scan (high recall)
2. DistilBERT binary classifier (learned features)
3. Combined score with safety override
"""

from __future__ import annotations

import logging
from typing import List

from backend.config import settings
from backend.database.schemas import CrisisResult
from backend.utils.constants import CRISIS_KEYWORDS

logger = logging.getLogger(__name__)

_model = None
_tokenizer = None


async def load_model() -> None:
    global _model, _tokenizer
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        logger.info("Loading crisis model from %s …", settings.CRISIS_MODEL_PATH)
        _tokenizer = AutoTokenizer.from_pretrained(settings.CRISIS_MODEL_PATH)
        _model = AutoModelForSequenceClassification.from_pretrained(
            settings.CRISIS_MODEL_PATH
        )
        _model.eval()
        logger.info("Crisis model loaded successfully.")
    except Exception:
        logger.warning(
            "Crisis model not found at %s – using keyword‑only detection.",
            settings.CRISIS_MODEL_PATH,
        )


def predict(text: str) -> CrisisResult:
    """
    Evaluate crisis risk for *preprocessed* text.
    Returns CrisisResult with combined probability and safety override flag.
    """
    keyword_prob, matched = _keyword_scan(text)
    model_prob = _model_predict(text)

    # Combine: take the MAX of both signals (high‑recall oriented)
    combined_prob = max(keyword_prob, model_prob)

    is_crisis = combined_prob >= settings.CRISIS_PROBABILITY_THRESHOLD
    safety_override = combined_prob >= settings.SAFETY_OVERRIDE_THRESHOLD

    if safety_override:
        logger.warning("SAFETY OVERRIDE triggered for input (prob=%.3f)", combined_prob)

    return CrisisResult(
        is_crisis=is_crisis,
        probability=round(combined_prob, 4),
        matched_keywords=matched,
        safety_override=safety_override,
    )


def _keyword_scan(text: str) -> tuple[float, List[str]]:
    """Rule‑based keyword detection – returns (probability, matched_keywords)."""
    matched = [kw for kw in CRISIS_KEYWORDS if kw in text]
    if not matched:
        return 0.0, []
    # Scale up rapidly with more keyword hits
    prob = min(1.0, 0.5 + 0.15 * len(matched))
    return prob, matched


def _model_predict(text: str) -> float:
    """Return crisis probability from the binary classifier (0‑1)."""
    if _model is None or _tokenizer is None:
        return 0.0

    import torch

    inputs = _tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        logits = _model(**inputs).logits
    probs = torch.nn.functional.softmax(logits, dim=-1).squeeze().tolist()
    # Assume index 1 = crisis
    return round(float(probs[1]), 4)
