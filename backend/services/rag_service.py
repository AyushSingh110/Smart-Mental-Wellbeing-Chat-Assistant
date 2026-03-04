from __future__ import annotations

import json
import logging
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from backend.services.llm_service import generate_llm_response

logger = logging.getLogger(__name__)

MODEL_NAME           = "all-MiniLM-L6-v2"
INDEX_PATH           = "backend/rag/faiss_index.index"
METADATA_PATH        = "backend/rag/metadata.json"
SIMILARITY_THRESHOLD = 2.0
TOP_K                = 3

# ── System prompt ─────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """
You are a Cognitive Behavioral Therapy (CBT)-based mental well-being assistant.

Your Purpose:
- Provide emotionally supportive, evidence-based coping guidance.
- Base your response ONLY on the retrieved CBT context provided.
- Adapt tone and length to the user's emotional state and risk level.
- Maintain a calm, empathetic, non-judgmental tone at all times.

Strict Rules:
- Use ONLY techniques grounded in the retrieved context.
- Do NOT invent new therapeutic methods or diagnoses.
- Do NOT provide medication recommendations.
- Do NOT minimize emotional distress.
- Do NOT validate self-harm or suicidal thoughts.
- NEVER use bullet points, headers, or lists — write in natural prose.

Safety Protocol:
- If crisis_tier is 'distress': validate first, then one brief coping suggestion.
- Never sound robotic or scripted.
- Do NOT overreact to mild everyday stress — read context carefully.

CRITICAL — Response Length:
You MUST follow the sentence limit instruction given below exactly.
Do not write more sentences than instructed.
End with ONE gentle, open, supportive question (counts as one sentence).
"""

# ── Category → prompt length instruction ─────────────────────────────────────
_LENGTH_INSTRUCTIONS: dict[str, str] = {
    "Stable": (
        "Write a warm, conversational response of EXACTLY 4 to 5 sentences. "
        "Keep it light and supportive. End with one open question."
    ),
    "Mild Stress": (
        "Write a supportive coaching response of EXACTLY 3 to 4 sentences. "
        "Validate first, then one brief coping suggestion. End with one question."
    ),
    "Moderate Distress": (
        "Write an emotional validation response of EXACTLY 2 to 3 sentences. "
        "Focus on making the user feel heard. One gentle question at the end."
    ),
    "High Risk": (
        "Write a SHORT, compassionate response of EXACTLY 1 to 2 sentences. "
        "Be warm and grounding. No advice — just presence. End with one question."
    ),
    "Depression Risk": (
        "Write a SHORT, compassionate response of EXACTLY 1 to 2 sentences. "
        "Be gentle and affirming. End with one simple question."
    ),
    # Crisis Risk is handled by safety_service — RAG is never called
}


class RAGService:

    def __init__(self):
        self.embed_model = SentenceTransformer(MODEL_NAME)
        self.index       = faiss.read_index(INDEX_PATH)
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

    # ── Context retrieval ─────────────────────────────────────────────────────

    def retrieve_context(self, query: str) -> list[dict]:
        embedding          = self.embed_model.encode([query])
        distances, indices = self.index.search(np.array(embedding), TOP_K)

        results = [
            self.metadata[idx]
            for i, idx in enumerate(indices[0])
            if distances[0][i] <= SIMILARITY_THRESHOLD
        ]
        if not results:
            results = [self.metadata[indices[0][0]]]   # always return at least one chunk

        return results

    # ── Prompt builder ────────────────────────────────────────────────────────

    def _build_prompt(
        self,
        user_message:  str,
        emotion_label: str,
        emotion_score: float,
        intent:        str,
        mhi:           float,
        crisis_score:  float,
        crisis_tier:   str,
        category:      str,
        chunks:        list[dict],
    ) -> str:
        context_text   = "\n\n".join(
            f"Technique {i+1}:\n{c['text']}" for i, c in enumerate(chunks)
        )
        length_instruction = _LENGTH_INSTRUCTIONS.get(
            category,
            "Write a concise, supportive response of 2 to 3 sentences."
        )

        return f"""{_SYSTEM_PROMPT}

Retrieved CBT Context:
{context_text}

User Emotional State:
- Dominant Emotion : {emotion_label} (score: {emotion_score:.2f})
- Intent           : {intent}
- Mental Health Index: {mhi}
- Crisis Probability : {crisis_score:.2f}
- Crisis Tier      : {crisis_tier}
- Category         : {category}

RESPONSE LENGTH INSTRUCTION (MANDATORY):
{length_instruction}

User Message:
{user_message}

Response Guidelines:
- Match tone to emotional state and category.
- If crisis_tier is 'distress': open with validation, then brief grounding.
- If crisis_tier is 'none' and category is 'Stable': warm reframing, no heavy advice.
- Do NOT name CBT techniques explicitly — integrate naturally.
- Write in plain prose. No bullet points. No headers.
- STRICTLY follow the sentence count instruction above.
"""

    # ── Main generate ─────────────────────────────────────────────────────────

    def generate_response(
        self,
        user_message:   str,
        emotion_label:  str,
        emotion_score:  float,
        intent:         str,
        mental_health_index: float,
        crisis_probability:  float,
        crisis_tier:    str  = "none",
        category:       str  = "Stable",
    ) -> tuple[str, bool]:
        """
        Returns (response_text, llm_failed).

        Crisis tiers (active / passive) should be intercepted by main.py
        before calling this — but if they somehow reach here, we return a
        safe stub and signal llm_failed=False so safety_service still
        applies the correct override.
        """
        # Should not be called for active/passive — safety net
        if crisis_tier in ("active", "passive"):
            logger.warning(
                "RAGService.generate_response called for crisis_tier=%s — "
                "returning empty so safety_service applies template",
                crisis_tier,
            )
            return "", False

        try:
            chunks  = self.retrieve_context(user_message)
            prompt  = self._build_prompt(
                user_message, emotion_label, emotion_score,
                intent, mental_health_index, crisis_probability,
                crisis_tier, category, chunks,
            )
            result  = generate_llm_response(prompt)

            if not result or not result.strip():
                logger.warning("RAGService | LLM returned empty response")
                return "", True   # signal failure

            return result, False

        except Exception as exc:
            logger.error("RAGService.generate_response error: %s", exc)
            return "", True   # signal failure → safety_service uses fallback
