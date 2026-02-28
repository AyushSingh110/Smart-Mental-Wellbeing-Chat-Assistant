"""
Intent recognition service.

Uses a Sentence Transformer to embed the user message and performs
nearest‑neighbour search against a small FAISS index of intent exemplars.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from backend.config import settings
from backend.database.schemas import IntentResult, IntentType
from backend.utils.constants import INTENT_LABELS

logger = logging.getLogger(__name__)

_embedder = None
_index = None
_intent_labels_index: list[str] = []

# ── Example intent exemplars (used to build initial index) ──
_INTENT_EXEMPLARS: dict[str, list[str]] = {
    "venting": [
        "I just need to talk about my day",
        "I feel so overwhelmed and just need to vent",
        "Everything is going wrong",
        "I had the worst day ever",
    ],
    "advice_seeking": [
        "What should I do about my anxiety?",
        "Can you give me some tips for stress?",
        "How do I deal with negative thoughts?",
        "I need advice on managing my emotions",
    ],
    "crisis": [
        "I want to hurt myself",
        "I don't want to be alive anymore",
        "I'm thinking about ending it",
        "I feel like there is no way out",
    ],
    "casual_talk": [
        "Hey, how are you?",
        "What can you do?",
        "Tell me a joke",
        "I'm just browsing",
    ],
    "assessment": [
        "I want to take the PHQ assessment",
        "Can I do a mental health screening?",
        "Start the questionnaire",
        "I'd like to check my mental health score",
    ],
}


async def load_model() -> None:
    """Build / load sentence embedder + FAISS index on startup."""
    global _embedder, _index, _intent_labels_index
    try:
        from sentence_transformers import SentenceTransformer
        import faiss

        logger.info("Loading sentence transformer: %s …", settings.SENTENCE_MODEL_NAME)
        _embedder = SentenceTransformer(settings.SENTENCE_MODEL_NAME)

        # Build a small FAISS index from exemplars
        all_sentences: list[str] = []
        for intent, sentences in _INTENT_EXEMPLARS.items():
            for s in sentences:
                all_sentences.append(s)
                _intent_labels_index.append(intent)

        embeddings = _embedder.encode(all_sentences, normalize_embeddings=True)
        dim = embeddings.shape[1]
        _index = faiss.IndexFlatIP(dim)
        _index.add(np.array(embeddings, dtype=np.float32))
        logger.info("Intent FAISS index built – %d vectors, dim=%d", len(all_sentences), dim)
    except Exception:
        logger.warning("Intent model / FAISS not available – using fallback.")


def predict(text: str) -> IntentResult:
    """Return the most likely intent for the given preprocessed text."""
    if _embedder is None or _index is None:
        return IntentResult(intent=IntentType.CASUAL_TALK, confidence=0.5)

    query = _embedder.encode([text], normalize_embeddings=True).astype(np.float32)
    scores, indices = _index.search(query, k=3)

    # Majority vote among top‑3 neighbours
    votes: dict[str, float] = {}
    for score, idx in zip(scores[0], indices[0]):
        label = _intent_labels_index[idx]
        votes[label] = votes.get(label, 0.0) + float(score)

    best_label = max(votes, key=votes.get)  # type: ignore[arg-type]
    confidence = round(votes[best_label] / sum(votes.values()), 4)

    return IntentResult(
        intent=IntentType(best_label),
        confidence=confidence,
    )
