from backend.rag.retriever import CBTVectorRetriever

retriever = CBTVectorRetriever()
retriever.load_index()

results = retriever.retrieve("I feel anxious and overwhelmed.")
for r in results:
    print("Score:", r["score"])
    print(r["text"])