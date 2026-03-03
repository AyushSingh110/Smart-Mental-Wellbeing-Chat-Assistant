from __future__ import annotations

from sentence_transformers import SentenceTransformer
import numpy as np

_INTENTS: dict[str, list[str]] = {
    "venting":      ["I feel overwhelmed", "I just want to talk", "nobody listens to me"],
    "advice":       ["what should I do", "help me figure this out", "I need guidance"],
    "crisis":       ["I want to die", "hurt myself", "end my life", "I want to disappear"],
    "casual":       ["hello", "how are you", "just checking in"],
    "reassurance":  ["am I going to be okay", "will this ever get better", "I feel lost"],
}


class IntentService:

    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.intent_embeddings = {
            k: self.model.encode(v, normalize_embeddings=True).mean(axis=0)
            for k, v in _INTENTS.items()
        }

    def predict(self, text: str) -> str:
        emb = self.model.encode(text, normalize_embeddings=True)
        scores = {k: float(np.dot(emb, v)) for k, v in self.intent_embeddings.items()}
        best = max(scores, key=scores.get)
        return best if scores[best] >= 0.55 else "unknown"