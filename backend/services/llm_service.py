from __future__ import annotations

import logging

from backend.config import settings

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - depends on local env
    genai = None

_model = None


def _get_model():
    global _model
    if _model is not None:
        return _model
    if genai is None or not settings.GEMINI_API_KEY:
        return None

    genai.configure(api_key=settings.GEMINI_API_KEY)
    _model = genai.GenerativeModel(
        settings.LLM_MODEL,
        generation_config={
            "temperature": settings.LLM_TEMPERATURE,
            "max_output_tokens": settings.LLM_MAX_TOKENS,
        },
    )
    return _model


def generate_llm_response(prompt: str) -> str:
    """
    Sends a fully constructed prompt to Gemini.
    Prompt engineering is handled upstream by the RAG service.
    """
    model = _get_model()
    if model is None:
        logger.warning("LLM provider unavailable; returning empty response for safety fallback")
        return ""

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
        return ""
