"""
LLM response generation service.

Constructs a safety‑aware prompt that includes:
  • System persona & safety rules
  • Retrieved RAG context
  • User emotional / crisis state
  • Conversation history (last N turns)

Calls OpenAI (or compatible) chat completion API.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from backend.config import settings
from backend.database.schemas import (
    CrisisResult,
    EmotionResult,
    MatrixResult,
    RAGContext,
)
from backend.utils.constants import CRISIS_ESCALATION_MESSAGE

logger = logging.getLogger(__name__)

_client = None  # openai.AsyncOpenAI


async def init_client() -> None:
    global _client
    try:
        from openai import AsyncOpenAI

        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("OpenAI async client initialised (model=%s).", settings.LLM_MODEL)
    except Exception as exc:
        logger.warning("OpenAI client init failed: %s – LLM responses disabled.", exc)


# ────────────────────────────────────────────────────────
# System prompt template
# ────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a compassionate, professional mental health support assistant.

RULES — follow these strictly:
1. NEVER provide medical diagnoses.
2. NEVER prescribe medication.
3. NEVER encourage self‑harm, suicide, or violence.
4. If the user is in crisis, ALWAYS include crisis hotline information.
5. Use evidence‑based CBT techniques drawn ONLY from the provided context.
6. Be empathetic, warm, and non‑judgmental.
7. Encourage professional help when appropriate.
8. If unsure, say so honestly — do not fabricate information.

USER STATE:
- Detected emotion: {emotion_label} (confidence {emotion_conf:.0%})
- Mental Health Index: {mhi:.0f}/100 ({category})
- Crisis flagged: {crisis_flag}

RELEVANT CBT CONTEXT (use this to ground your answer):
{rag_context}
"""


async def generate(
    user_message: str,
    emotion: EmotionResult,
    crisis: CrisisResult,
    matrix: MatrixResult,
    rag_context: RAGContext,
    history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    Generate a grounded, safety‑aware response.
    Falls back to a safe canned message if the LLM is unavailable.
    """
    # ── Safety‑override path ────────────────────────────
    if crisis.safety_override:
        return CRISIS_ESCALATION_MESSAGE

    # ── Construct messages list ─────────────────────────
    rag_text = "\n---\n".join(rag_context.documents) if rag_context.documents else "(no relevant documents retrieved)"

    system_content = _SYSTEM_PROMPT.format(
        emotion_label=emotion.label,
        emotion_conf=emotion.confidence,
        mhi=matrix.mhi,
        category=matrix.category.value,
        crisis_flag="YES ⚠️" if crisis.is_crisis else "No",
        rag_context=rag_text,
    )

    messages: list[dict[str, str]] = [{"role": "system", "content": system_content}]

    # Append recent conversation history for continuity
    if history:
        for turn in history[-6:]:  # last 3 exchanges
            messages.append(turn)

    messages.append({"role": "user", "content": user_message})

    # ── If crisis detected but not override, prepend warning note
    if crisis.is_crisis:
        messages.append(
            {
                "role": "system",
                "content": (
                    "IMPORTANT: The user may be in distress. Include crisis resources "
                    "in your response and speak with extra care."
                ),
            }
        )

    # ── Call LLM ────────────────────────────────────────
    if _client is None:
        return _fallback_response(emotion, crisis, matrix)

    try:
        completion = await _client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )
        response_text = completion.choices[0].message.content or ""
        return response_text.strip()
    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        return _fallback_response(emotion, crisis, matrix)


def _fallback_response(
    emotion: EmotionResult,
    crisis: CrisisResult,
    matrix: MatrixResult,
) -> str:
    """Safe canned response when the LLM is unreachable."""
    if crisis.is_crisis:
        return CRISIS_ESCALATION_MESSAGE
    return (
        "Thank you for sharing. I'm here to listen and support you. "
        "It sounds like you might be feeling some "
        f"{emotion.label}. Remember, it's okay to feel this way, "
        "and reaching out is a sign of strength. "
        "Would you like to try a grounding exercise or talk more about what's on your mind?"
    )
