from __future__ import annotations

import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from backend.services.llm_service import generate_llm_response

MODEL_NAME  = "all-MiniLM-L6-v2"
INDEX_PATH  = "backend/rag/faiss_index.index"
METADATA_PATH = "backend/rag/metadata.json"
SIMILARITY_THRESHOLD = 2.0
TOP_K = 3

_SYSTEM_PROMPT = """
You are a structured Cognitive Behavioral Therapy (CBT)-based mental well-being assistant.

Your Purpose:
- Provide emotionally supportive, evidence-based coping guidance.
- Base your response primarily on the retrieved CBT context.
- Adapt guidance to the user's emotional state, mental health index, and crisis tier.
- Maintain a calm, empathetic, and non-judgmental tone at all times.

Strict Rules:
- Use ONLY techniques or concepts grounded in the retrieved context.
- Do NOT invent new therapeutic methods.
- Do NOT provide medical diagnoses or medication recommendations.
- Do NOT minimize emotional distress.
- Do NOT validate self-harm or suicidal thoughts.

Safety Protocol:
- If crisis_tier is 'active' or 'passive': prioritize immediate safety validation before coping.
- Gently but clearly encourage reaching out to real people or professionals.
- Never sound robotic, scripted, or dismissive.
- Do NOT overreact to mild sadness — read context carefully.

Response Tone by MHI:
- MHI >= 65: warm, supportive, light CBT reframing
- MHI 45–64: structured coping guidance, validate first
- MHI < 45: safety-first language, empathetic, step-by-step grounding

Apply CBT principles conversationally. Do not name techniques explicitly.
End with one gentle, open, supportive question.
"""


class RAGService:

    def __init__(self):
        self.model    = SentenceTransformer(MODEL_NAME)
        self.index    = faiss.read_index(INDEX_PATH)
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

    def retrieve_context(self, query: str) -> list[dict]:
        embedding = self.model.encode([query])
        distances, indices = self.index.search(np.array(embedding), TOP_K)

        results = [
            self.metadata[idx]
            for i, idx in enumerate(indices[0])
            if distances[0][i] <= SIMILARITY_THRESHOLD
        ]

        # Fallback: always return at least one chunk
        if not results:
            results = [self.metadata[indices[0][0]]]

        return results

    def _build_prompt(
        self,
        user_message: str,
        emotion_label: str,
        emotion_score: float,
        intent: str,
        mhi: float,
        crisis_score: float,
        crisis_tier: str,
        chunks: list[dict],
    ) -> str:
        context_text = "\n\n".join(
            f"Technique {i + 1}:\n{c['text']}" for i, c in enumerate(chunks)
        )

        if mhi < 45:
            depth = "Use safety-first language. Prioritize emotional grounding before coping strategies."
        elif mhi < 65:
            depth = "Provide moderate structured coping guidance with clear validation."
        else:
            depth = "Provide warm supportive reframing. Keep it conversational and light."

        return f"""{_SYSTEM_PROMPT}

Retrieved CBT Context:
{context_text}

User Emotional State:
- Dominant Emotion: {emotion_label} (score: {emotion_score:.2f})
- Intent: {intent}
- Mental Health Index: {mhi}
- Crisis Probability: {crisis_score:.2f}
- Crisis Tier: {crisis_tier}

Response Depth Instruction:
{depth}

User Message:
{user_message}

Instructions:
- Ground your response in the retrieved CBT context.
- Match tone to the user's emotional state and crisis tier.
- If crisis_tier is 'active' or 'passive': open with direct safety acknowledgment.
- If crisis_tier is 'distress': validate first, then offer grounding.
- If crisis_tier is 'none': respond empathetically with CBT-based support.
- Do NOT list techniques by name. Integrate them naturally.
- End with one gentle, reflective question.
"""

    def generate_response(
        self,
        user_message: str,
        emotion_label: str,
        emotion_score: float,
        intent: str,
        mental_health_index: float,
        crisis_probability: float,
        crisis_tier: str = "none",
    ) -> str:
        # Safety_service handles the full override — RAG still generates
        # the human-facing response for passive/distress tiers so the
        # safety_service can append to it rather than replace it entirely.
        chunks  = self.retrieve_context(user_message)
        prompt  = self._build_prompt(
            user_message, emotion_label, emotion_score,
            intent, mental_health_index, crisis_probability,
            crisis_tier, chunks,
        )
        return generate_llm_response(prompt)