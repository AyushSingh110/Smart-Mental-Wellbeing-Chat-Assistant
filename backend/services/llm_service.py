from __future__ import annotations

import logging

import google.generativeai as genai

from backend.config import settings

logger = logging.getLogger(__name__)

# -- Configure Gemini from centralised settings --------------------------------

genai.configure(api_key=settings.GEMINI_API_KEY)

MODEL_NAME = "gemini-2.5-flash-lite"

model = genai.GenerativeModel(
    MODEL_NAME,
    generation_config={
        "temperature": settings.LLM_TEMPERATURE,
        "max_output_tokens": settings.LLM_MAX_TOKENS,
    },
)


def generate_llm_response(prompt: str) -> str:
    """
    Sends a fully constructed prompt to Gemini.
    Prompt engineering is handled upstream by the RAG service.
    """
    try:
        response = model.generate_content(prompt)

        if hasattr(response, "text") and response.text:
            return response.text.strip()

        logger.warning("LLM returned empty response object")
        return (
            "I'm here to support you. I couldn't generate a response just now. "
            "If you're feeling overwhelmed, please consider reaching out to a trusted person."
        )

    except Exception as exc:
        logger.error("LLM generation error: %s", exc)
        return (
            "I'm here to support you. There was a technical issue generating a response. "
            "If you're feeling overwhelmed, consider reaching out to someone you trust."
        )