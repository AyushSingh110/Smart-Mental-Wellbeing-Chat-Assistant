from sentence_transformers import SentenceTransformer
import numpy as np

INTENTS = {
    "venting": ["I feel overwhelmed", "just want to talk"],
    "advice": ["what should I do", "help me"],
    "crisis": ["I want to die", "hurt myself"],
    "casual": ["hello", "how are you"]
}

class IntentService:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.intent_embeddings = {
            k: self.model.encode(v, normalize_embeddings=True).mean(axis=0)
            for k, v in INTENTS.items()
        }

    def predict(self, text):
        emb = self.model.encode(text, normalize_embeddings=True)
        scores = {
            intent: np.dot(emb, vec)
            for intent, vec in self.intent_embeddings.items()
        }
        best = max(scores, key=scores.get)
        return best if scores[best] >= 0.6 else "unknown"