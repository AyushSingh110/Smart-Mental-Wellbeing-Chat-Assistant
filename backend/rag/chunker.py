import os
from typing import List, Dict

def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap

    return chunks


def load_and_chunk_documents(base_path: str) -> List[Dict]:
    all_chunks = []

    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()

                chunks = chunk_text(text)

                for i, chunk in enumerate(chunks):
                    all_chunks.append({
                        "text": chunk,
                        "source_file": file,
                        "chunk_id": f"{file}_chunk_{i}"
                    })

    return all_chunks