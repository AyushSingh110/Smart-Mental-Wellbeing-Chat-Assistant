import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer
from chunker import load_and_chunk_documents

MODEL_NAME = "all-MiniLM-L6-v2"
DOC_PATH = "backend/rag/cbt_documents"
INDEX_PATH = "backend/rag/faiss_index.index"
METADATA_PATH = "backend/rag/metadata.json"

def build_faiss_index():

    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    print("Loading and chunking documents...")
    chunks = load_and_chunk_documents(DOC_PATH)

    texts = [chunk["text"] for chunk in chunks]

    print("Generating embeddings...")
    embeddings = model.encode(texts, show_progress_bar=True)

    dimension = embeddings.shape[1]

    print("Creating FAISS index...")
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))

    print("Saving index...")
    faiss.write_index(index, INDEX_PATH)

    print("Saving metadata...")
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)

    print("FAISS index built successfully!")

if __name__ == "__main__":
    build_faiss_index()