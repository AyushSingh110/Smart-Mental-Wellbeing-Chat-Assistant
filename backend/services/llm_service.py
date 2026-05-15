from __future__ import annotations

import logging

from backend.config import settings

logger = logging.getLogger(__name__)

# Try new google.genai SDK first, fall back to deprecated google.generativeai
_use_new_sdk = False
_genai_new = None
_genai_old = None

try:
    from google import genai as _genai_new
    _use_new_sdk = True
    logger.info("LLM | Using google.genai SDK (new)")
except ImportError:
    try:
        import google.generativeai as _genai_old  # type: ignore[import]
        logger.info("LLM | Using google.generativeai SDK (legacy)")
    except ImportError:
        logger.warning("LLM | No Gemini SDK available. Install google-genai.")

# Lazy-initialised clients
_client = None    # new SDK: genai.Client
_model = None     # old SDK: GenerativeModel


def _get_client_new():
    global _client
    if _client is not None:
        return _client
    if not settings.GEMINI_API_KEY:
        return None
    _client = _genai_new.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def _get_model_old():
    global _model
    if _model is not None:
        return _model
    if _genai_old is None or not settings.GEMINI_API_KEY:
        return None
    _genai_old.configure(api_key=settings.GEMINI_API_KEY)
    _model = _genai_old.GenerativeModel(
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
    Tries new google.genai SDK first, falls back to deprecated SDK.
    """
    if _use_new_sdk:
        return _generate_new_sdk(prompt)
    return _generate_old_sdk(prompt)


def _generate_new_sdk(prompt: str) -> str:
    from google.genai import types

    client = _get_client_new()
    if client is None:
        logger.warning("LLM | Gemini API key not set; returning empty for safety fallback")
        return ""
    try:
        response = client.models.generate_content(
            model=settings.LLM_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=settings.LLM_TEMPERATURE,
                max_output_tokens=settings.LLM_MAX_TOKENS,
            ),
        )
        text = getattr(response, "text", None)
        if text and text.strip():
            return text.strip()
        logger.warning("LLM | Gemini returned empty response")
        return (
            "I'm here to support you. I couldn't generate a response just now. "
            "If you're feeling overwhelmed, please consider reaching out to a trusted person."
        )
    except Exception as exc:
        logger.error("LLM | generation error (new SDK): %s", exc)
        return ""


def _generate_old_sdk(prompt: str) -> str:
    model = _get_model_old()
    if model is None:
        logger.warning("LLM | provider unavailable; returning empty for safety fallback")
        return ""
    try:
        response = model.generate_content(prompt)
        if hasattr(response, "text") and response.text:
            return response.text.strip()
        logger.warning("LLM | returned empty response object")
        return (
            "I'm here to support you. I couldn't generate a response just now. "
            "If you're feeling overwhelmed, please consider reaching out to a trusted person."
        )
    except Exception as exc:
        logger.error("LLM | generation error (legacy SDK): %s", exc)
        return ""
