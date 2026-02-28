"""
RAG retrieval service.

Embeds the user query with Sentence Transformers and retrieves the
top‑K most relevant CBT module chunks from the FAISS vector store.
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional

import numpy as np

from backend.config import settings
from backend.database.schemas import RAGContext

logger = logging.getLogger(__name__)

_embedder = None
_index = None
_chunks: list[dict] = []  # {"text": ..., "source": ...}


async def load_index() -> None:
    """Load the pre‑built FAISS CBT index and metadata on startup."""
    global _embedder, _index, _chunks
    try:
        import faiss
        import json
        from sentence_transformers import SentenceTransformer

        _embedder = SentenceTransformer(settings.SENTENCE_MODEL_NAME)

        index_path = settings.FAISS_INDEX_PATH
        meta_path = os.path.join(index_path, "metadata.json")
        faiss_path = os.path.join(index_path, "index.faiss")

        if os.path.exists(faiss_path) and os.path.exists(meta_path):
            _index = faiss.read_index(faiss_path)
            with open(meta_path, "r", encoding="utf-8") as f:
                _chunks = json.load(f)
            logger.info(
                "RAG FAISS index loaded – %d chunks from %s",
                _index.ntotal,
                faiss_path,
            )
        else:
            logger.warning(
                "RAG FAISS index not found at %s – retrieval will return empty.",
                index_path,
            )
    except Exception as exc:
        logger.warning("RAG index load failed: %s – retrieval disabled.", exc)


def retrieve(query: str, top_k: Optional[int] = None) -> RAGContext:
    """Return the top‑K CBT chunks most relevant to the query."""
    k = top_k or settings.RAG_TOP_K

    if _embedder is None or _index is None or _index.ntotal == 0:
        return RAGContext(documents=[], sources=[])

    q_vec = _embedder.encode([query], normalize_embeddings=True).astype(np.float32)
    distances, indices = _index.search(q_vec, k)

    documents: List[str] = []
    sources: List[str] = []
    for idx in indices[0]:
        if 0 <= idx < len(_chunks):
            documents.append(_chunks[idx]["text"])
            sources.append(_chunks[idx].get("source", "unknown"))

    return RAGContext(documents=documents, sources=sources)
