import json
import faiss
import numpy as np
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from backend.config import settings


class CBTVectorRetriever:
    """
    Handles semantic retrieval of CBT documents using FAISS.
    """

    def __init__(self):
        self.embedding_model = SentenceTransformer(settings.SENTENCE_MODEL_NAME)
        self.index = None
        self.metadata = None

    def load_index(self):
        """
        Load FAISS index and metadata into memory.
        """
        self.index = faiss.read_index(settings.FAISS_INDEX_PATH)

        with open(settings.FAISS_METADATA_PATH, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

    def embed_query(self, query: str) -> np.ndarray:
        """
        Convert user query into embedding vector.
        """
        embedding = self.embedding_model.encode(
            query,
            normalize_embeddings=True
        )
        return np.array([embedding])

    def retrieve(self, query: str, top_k: int = None) -> List[Dict]:
        """
        Retrieve top-k relevant CBT chunks for the query.
        """
        if self.index is None or self.metadata is None:
            raise RuntimeError("FAISS index not loaded. Call load_index() first.")

        top_k = top_k or settings.RAG_TOP_K

        query_embedding = self.embed_query(query)

        distances, indices = self.index.search(query_embedding, top_k)

        results = []

        for i, idx in enumerate(indices[0]):
            if idx == -1:
                continue

            chunk = self.metadata[idx]
            chunk["score"] = float(distances[0][i])
            results.append(chunk)

        return results