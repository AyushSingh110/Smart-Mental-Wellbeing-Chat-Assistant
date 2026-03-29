from __future__ import annotations

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - depends on local env
    SentenceTransformer = None

_KEYWORD_FALLBACK: dict[str, tuple[str, ...]] = {
    "venting": ("overwhelmed", "tired", "exhausted", "upset", "sad", "stressed"),
    "advice": ("what should i do", "help me", "guidance", "advice", "suggest"),
    "crisis": ("want to die", "hurt myself", "end my life", "disappear", "kill myself"),
    "casual": ("hello", "hi", "how are you", "checking in"),
    "reassurance": ("will i be okay", "get better", "feel lost", "okay right now"),
}

_INTENTS: dict[str, list[str]] = {
    "venting":      ["I feel overwhelmed", "I just want to talk", "nobody listens to me"],
    "advice":       ["what should I do", "help me figure this out", "I need guidance"],
    "crisis":       ["I want to die", "hurt myself", "end my life", "I want to disappear"],
    "casual":       ["hello", "how are you", "just checking in"],
    "reassurance":  ["am I going to be okay", "will this ever get better", "I feel lost"],
}


class IntentService:

    def __init__(self):
        self.model = None
        self.intent_embeddings = {}
        try:
            if SentenceTransformer is not None:
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
                self.intent_embeddings = {
                    k: self.model.encode(v, normalize_embeddings=True).mean(axis=0)
                    for k, v in _INTENTS.items()
                }
        except Exception:
            self.model = None
            self.intent_embeddings = {}

    def predict(self, text: str) -> str:
        if self.model is None:
            lowered = text.lower()
            for intent, keywords in _KEYWORD_FALLBACK.items():
                if any(keyword in lowered for keyword in keywords):
                    return intent
            return "unknown"
        emb = self.model.encode(text, normalize_embeddings=True)
        scores = {k: float(np.dot(emb, v)) for k, v in self.intent_embeddings.items()}
        best = max(scores, key=scores.get)
        return best if scores[best] >= 0.55 else "unknown"
