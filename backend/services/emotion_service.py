"""
Emotion classification service.

Wraps a fine‑tuned DistilBERT model (GoEmotions → mapped labels).
At startup the model + tokenizer are loaded once; inference is sync
but runs fast on CPU for single‑sentence inputs.
"""

from __future__ import annotations

import logging
from typing import Dict

from backend.config import settings
from backend.database.schemas import EmotionResult
from backend.utils.constants import EMOTION_LABELS

logger = logging.getLogger(__name__)

# ── Lazy‑loaded globals (populated by load_model) ───
_model = None
_tokenizer = None


async def load_model() -> None:
    """Called once during FastAPI startup to warm the model."""
    global _model, _tokenizer
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        logger.info("Loading emotion model from %s …", settings.EMOTION_MODEL_PATH)
        _tokenizer = AutoTokenizer.from_pretrained(settings.EMOTION_MODEL_PATH)
        _model = AutoModelForSequenceClassification.from_pretrained(
            settings.EMOTION_MODEL_PATH
        )
        _model.eval()
        logger.info("Emotion model loaded successfully.")
    except Exception:
        logger.warning(
            "Emotion model not found at %s – falling back to dummy predictions.",
            settings.EMOTION_MODEL_PATH,
        )


def predict(text: str) -> EmotionResult:
    """
    Run emotion classification on *preprocessed* text.
    Returns an EmotionResult with label, scores dict, and confidence.
    """
    if _model is None or _tokenizer is None:
        return _dummy_predict(text)

    import torch

    inputs = _tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        logits = _model(**inputs).logits
    probs = torch.nn.functional.softmax(logits, dim=-1).squeeze().tolist()

    scores: Dict[str, float] = {
        label: round(prob, 4) for label, prob in zip(EMOTION_LABELS, probs)
    }
    dominant_label = max(scores, key=scores.get)  # type: ignore[arg-type]
    return EmotionResult(
        label=dominant_label,
        scores=scores,
        confidence=scores[dominant_label],
    )


# ── Fallback when model files are absent ─────────────

def _dummy_predict(text: str) -> EmotionResult:
    """Deterministic placeholder so the API layer always works."""
    scores = {label: round(1.0 / len(EMOTION_LABELS), 4) for label in EMOTION_LABELS}
    scores["neutral"] = round(1.0 - sum(v for k, v in scores.items() if k != "neutral"), 4)
    return EmotionResult(label="neutral", scores=scores, confidence=scores["neutral"])
