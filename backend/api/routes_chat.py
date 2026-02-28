"""
POST /chat  –  Main chat pipeline route.

Orchestrates the full 10‑step pipeline:
  1. Receive message
  2. Preprocess
  3. Run emotion model
  4. Run intent model
  5. Run crisis model
  6. Calculate Mental Health Matrix
  7. Retrieve RAG documents
  8. Generate LLM response (with safety prompt)
  9. Store all results in MongoDB
 10. Return response
"""

from __future__ import annotations

import logging
import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from backend.database.mongo_client import MongoClient
from backend.database.schemas import (
    ChatRequest,
    ChatResponse,
    PipelineResult,
)
from backend.dependencies import get_db
from backend.services import (
    crisis_service,
    emotion_service,
    intent_service,
    llm_service,
    matrix_service,
    rag_service,
    safety_service,
)
from backend.utils.preprocessing import preprocess

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


# ────────────────────────────────────────────────────────
# POST /chat
# ────────────────────────────────────────────────────────

@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Process a user message through the full analysis pipeline",
    responses={
        422: {"description": "Validation error (missing user_id / message)"},
        500: {"description": "Internal pipeline error"},
    },
)
async def chat(
    body: ChatRequest,
    db: MongoClient = Depends(get_db),
) -> ChatResponse:
    """
    End‑to‑end mental‑health chat pipeline.

    Accepts `{ user_id, message }` and returns a fully annotated response
    including emotion, intent, crisis status, MHI score, and the LLM‑
    generated support message.
    """
    start = time.perf_counter()

    try:
        # ── 0. Fetch / create user profile ──────────────
        user = await db.get_or_create_user(body.user_id)

        # ── 1. Preprocess ───────────────────────────────
        cleaned = preprocess(body.message)
        logger.info("[%s] Preprocessed: %s", body.user_id, cleaned[:80])

        # ── 2. Emotion classification ───────────────────
        emotion = emotion_service.predict(cleaned)
        logger.info("[%s] Emotion: %s (%.2f)", body.user_id, emotion.label, emotion.confidence)

        # ── 3. Intent recognition ───────────────────────
        intent = intent_service.predict(cleaned)
        logger.info("[%s] Intent: %s (%.2f)", body.user_id, intent.intent.value, intent.confidence)

        # ── 4. Crisis detection ─────────────────────────
        crisis = crisis_service.predict(cleaned)
        if crisis.is_crisis:
            logger.warning("[%s] ⚠️  Crisis detected (prob=%.3f)", body.user_id, crisis.probability)

        # ── 5. Historical trend from DB ─────────────────
        historical_trend = await db.compute_historical_trend_score(body.user_id)

        # ── 6. Mental Health Matrix ─────────────────────
        matrix = matrix_service.calculate(
            emotion=emotion,
            crisis=crisis,
            screening_normalized=user.get("screening_normalized", 0.0),
            behavioral_score=user.get("behavioral_score", 0.0),
            historical_trend_score=historical_trend,
        )
        logger.info(
            "[%s] MHI=%.1f  Category=%s  TRS=%.3f",
            body.user_id, matrix.mhi, matrix.category.value, matrix.trs,
        )

        # ── 7. RAG retrieval ───────────────────────────
        rag_context = rag_service.retrieve(cleaned)

        # ── 8. LLM response generation ─────────────────
        history = await _build_history(db, body.user_id)
        llm_response = await llm_service.generate(
            user_message=body.message,
            emotion=emotion,
            crisis=crisis,
            matrix=matrix,
            rag_context=rag_context,
            history=history,
        )

        # ── 8b. Post‑generation safety filter ──────────
        llm_response, safety_flagged = safety_service.validate_response(llm_response)

        # ── 9. Persist to MongoDB ───────────────────────
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

        conversation_doc = {
            "user_id": body.user_id,
            "message": body.message,
            "preprocessed_text": cleaned,
            "response": llm_response,
            "emotion": emotion.model_dump(),
            "intent": intent.model_dump(),
            "crisis": crisis.model_dump(),
            "matrix": matrix.model_dump(),
            "safety_flagged": safety_flagged,
            "processing_time_ms": elapsed_ms,
            "timestamp": datetime.utcnow(),
        }
        await db.store_conversation(conversation_doc)

        # Update user profile with latest scores
        await db.update_user_after_chat(
            user_id=body.user_id,
            mhi=matrix.mhi,
            category=matrix.category.value,
            behavioral_score=user.get("behavioral_score", 0.0),
            historical_trend_score=historical_trend,
        )

        logger.info("[%s] Pipeline complete in %.1f ms", body.user_id, elapsed_ms)

        # ── 10. Return response with all metrics ───────
        return ChatResponse(
            user_id=body.user_id,
            message=body.message,
            preprocessed_text=cleaned,
            response=llm_response,
            emotion=emotion,
            intent=intent,
            crisis=crisis,
            mental_health=matrix,
            safety_flagged=safety_flagged,
            processing_time_ms=elapsed_ms,
            timestamp=datetime.utcnow(),
        )

    except Exception as exc:
        logger.exception("Pipeline error for user %s: %s", body.user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing your message. Please try again.",
        )


# ────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────

async def _build_history(db: MongoClient, user_id: str) -> list[dict[str, str]]:
    """
    Fetch the last few conversation turns and format them as
    OpenAI‑style message dicts for the LLM context window.
    """
    recent = await db.get_recent_conversations(user_id, limit=6)
    history: list[dict[str, str]] = []
    for turn in reversed(recent):  # oldest first
        history.append({"role": "user", "content": turn["message"]})
        history.append({"role": "assistant", "content": turn["response"]})
    return history
