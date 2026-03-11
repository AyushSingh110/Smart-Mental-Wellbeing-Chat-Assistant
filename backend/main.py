from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from functools import partial

from fastapi import FastAPI, Query, Depends, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from bson import ObjectId

from backend.auth.auth_router import router as auth_router
from backend.config import settings
from backend.database.mongo_client import db
from backend.database.schemas import (
    ChatRequest,
    ChatResponse,
    AssessmentRequest,
    SpeakRequest,
)
from backend.dependencies import get_current_user
from backend.routes.routes_report import router as report_router

from backend.services.emotion_service import EmotionService
from backend.services.crisis_service import CrisisService
from backend.services.intent_service import IntentService
from backend.services.matrix_service import MentalHealthMatrix
from backend.services.rag_service import RAGService
from backend.services.safety_service import SafetyService
from backend.services.behavioral_service import BehavioralService
from backend.services.screening_service import ScreeningService
from backend.services.history_service import HistoryService
from backend.services.multilingual_voice_service import MultilingualVoiceService


# -- Logging -------------------------------------------------------------------

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# -- Services (instantiated once at startup, reused for every request) ---------

emotion_service    = EmotionService()
crisis_service     = CrisisService()
intent_service     = IntentService()
matrix_service     = MentalHealthMatrix()
rag_service        = RAGService()
safety_service     = SafetyService()
behavioral_service = BehavioralService()
screening_service  = ScreeningService()
history_service    = HistoryService(db.conversations)
voice_service      = MultilingualVoiceService()


# -- Lifespan ------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s …", settings.APP_NAME, settings.APP_VERSION)
    try:
        await db.create_indexes()
    except Exception as exc:
        logger.warning("Non-fatal: could not create DB indexes at startup: %s", exc)
    yield
    db.close()
    logger.info("Shutdown complete.")


# -- App -----------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Mental health chat API with emotion/crisis detection, "
        "MHI scoring, CBT-guided LLM responses, and voice support."
    ),
    lifespan=lifespan,
)

# Collect every origin the frontend might send
_ALLOWED_ORIGINS = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    settings.FRONTEND_URL,
    "null",
]

app.add_middleware(                    
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_origin_regex=r"http://localhost:\d+", 
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
    expose_headers=["Content-Disposition"],  
    max_age=600,   
)


# Routers — registered AFTER middleware
app.include_router(auth_router)
app.include_router(report_router)


# Thread-pool helper

async def _run_in_thread(fn, *args, **kwargs):
    """
    Offloads a synchronous blocking call (ML inference, STT, TTS) to
    FastAPI's default thread pool so the async event loop is never blocked.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(fn, *args, **kwargs))


# DB persistence helper 

async def _persist(
    user_id,
    message: str,
    emotion_scores: dict,
    crisis_score: float,
    crisis_tier: str,
    behavioral_score: float,
    screening_score: float,
    history_score: float,
    intent: str,
    mhi: float,
    category: str,
) -> None:
    """Saves one conversation turn to MongoDB. Used by all /chat exit paths."""
    await db.conversations.insert_one({
        "user_id":          user_id,
        "timestamp":        datetime.utcnow(),
        "message":          message,
        "emotion_scores":   emotion_scores,
        "crisis_score":     round(crisis_score, 4),
        "crisis_tier":      crisis_tier,
        "behavioral_score": round(behavioral_score, 4),
        "screening_score":  round(screening_score, 4),
        "history_score":    round(history_score, 4),
        "intent":           intent,
        "mhi":              int(mhi),
        "category":         category,
    })



# Routes
@app.get("/", summary="API info")
def root():
    return {
        "app":     settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs":    "/docs",
        "endpoints": {
            "POST /chat":             "Text analysis + LLM response pipeline",
            "POST /voice/transcribe": "Audio → transcript  (STT)",
            "POST /voice/speak":      "Text → audio bytes  (TTS)",
            "POST /assessment":       "Submit PHQ-2 / GAD-2 scores",
            "GET  /user/history":     "Paginated conversation history",
            "GET  /user/timeline":    "MHI timeline for dashboard chart",
            "GET  /report":           "Download PDF session report",
        },
    }



@app.options("/voice/transcribe", include_in_schema=False)
async def options_voice_transcribe():
    """
    Explicit OPTIONS handler for the STT endpoint.
    The CORSMiddleware already handles this, but having an explicit
    handler ensures a clean 200 and eliminates any router-level 405.
    """
    return Response(
        status_code=200,
        headers={
            "Allow": "POST, OPTIONS",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
        },
    )


@app.options("/voice/speak", include_in_schema=False)
async def options_voice_speak():
    """Explicit OPTIONS handler for the TTS endpoint."""
    return Response(
        status_code=200,
        headers={
            "Allow": "POST, OPTIONS",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
        },
    )


@app.options("/chat", include_in_schema=False)
async def options_chat():
    """Explicit OPTIONS handler for the chat endpoint."""
    return Response(
        status_code=200,
        headers={
            "Allow": "POST, OPTIONS",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
        },
    )


#  POST /chat 

@app.post("/chat", response_model=ChatResponse, summary="Full chat pipeline")
async def chat(
    body: ChatRequest,
    user_id: ObjectId = Depends(get_current_user),
):
    # Step 1: ML inference — offloaded to thread pool
    emotion_scores   = await _run_in_thread(emotion_service.predict, body.message)
    emotion_label    = max(emotion_scores, key=emotion_scores.get)
    emotion_score    = emotion_scores[emotion_label]

    crisis_score     = await _run_in_thread(crisis_service.predict,       body.message)
    crisis_tier      = await _run_in_thread(crisis_service.classify_tier, body.message)

    intent           = await _run_in_thread(intent_service.predict, body.message)
    behavioral_score = behavioral_service.predict(body.message)     # pure regex — fast

    logger.debug(
        "msg=%r | emotion=%s(%.2f) | crisis=%.3f | tier=%s | behavioral=%.2f",
        body.message[:60], emotion_label, emotion_score,
        crisis_score, crisis_tier, behavioral_score,
    )

    # Step 2: Async DB-dependent scoring
    history_score = await history_service.compute(user_id)

    user_doc = await db.users.find_one(
        {"_id": user_id},
        {"phq2_total": 1, "gad2_total": 1},
    )
    phq2 = int(user_doc.get("phq2_total", 0)) if user_doc else 0
    gad2 = int(user_doc.get("gad2_total", 0)) if user_doc else 0
    screening_score = screening_service.compute(phq2, gad2)

    # Step 3: Compute MHI (includes hopeless-phrase penalty + crisis ceilings)
    mhi = matrix_service.compute(
        emotion_score    = emotion_score,
        crisis_score     = crisis_score,
        emotion_label    = emotion_label,
        screening_score  = screening_score,
        behavioral_score = behavioral_score,
        history_score    = history_score,
        crisis_tier      = crisis_tier,
        raw_text         = body.message,
    )
    category = matrix_service.categorize(mhi, crisis_score, crisis_tier)

    logger.debug(
        "mhi=%d | category=%s | screening=%.2f | history=%.2f",
        mhi, category, screening_score, history_score,
    )

    # Step 4: Crisis early-exit — skip RAG for active/passive tiers
    if safety_service.is_active_crisis(
        crisis_tier, crisis_score, settings.SAFETY_OVERRIDE_THRESHOLD
    ):
        logger.info(
            "ACTIVE CRISIS early-exit | tier=%s score=%.3f | RAG skipped",
            crisis_tier, crisis_score,
        )
        final_response = safety_service.validate_response(
            response     = "",
            crisis_score = crisis_score,
            crisis_tier  = crisis_tier,
            category     = category,
            llm_failed   = False,
        )
        await _persist(
            user_id, body.message, emotion_scores, crisis_score, crisis_tier,
            behavioral_score, screening_score, history_score, intent, mhi, category,
        )
        return ChatResponse(
            response=final_response, emotion_scores=emotion_scores,
            crisis_score=round(crisis_score, 4), crisis_tier=crisis_tier,
            intent=intent, mhi=int(mhi), category=category,
        )

    if safety_service.is_passive_crisis(
        crisis_tier, crisis_score, settings.CRISIS_PROBABILITY_THRESHOLD
    ):
        logger.info(
            "PASSIVE CRISIS early-exit | tier=%s score=%.3f | RAG skipped",
            crisis_tier, crisis_score,
        )
        final_response = safety_service.validate_response(
            response     = "",
            crisis_score = crisis_score,
            crisis_tier  = crisis_tier,
            category     = category,
            llm_failed   = False,
        )
        await _persist(
            user_id, body.message, emotion_scores, crisis_score, crisis_tier,
            behavioral_score, screening_score, history_score, intent, mhi, category,
        )
        return ChatResponse(
            response=final_response, emotion_scores=emotion_scores,
            crisis_score=round(crisis_score, 4), crisis_tier=crisis_tier,
            intent=intent, mhi=int(mhi), category=category,
        )

    # Step 5: RAG-augmented LLM response
    llm_response, llm_failed = await _run_in_thread(
        rag_service.generate_response,
        body.message,
        emotion_label,
        emotion_score,
        intent,
        mhi,
        crisis_score,
        crisis_tier,
        category,
        body.language_code,
    )

    # Step 6: Safety validation + length trim
    final_response = safety_service.validate_response(
        response     = llm_response,
        crisis_score = crisis_score,
        crisis_tier  = crisis_tier,
        category     = category,
        llm_failed   = llm_failed,
    )

    # Step 7: Persist to MongoDB
    await _persist(
        user_id, body.message, emotion_scores, crisis_score, crisis_tier,
        behavioral_score, screening_score, history_score, intent, mhi, category,
    )

    return ChatResponse(
        response=final_response,
        emotion_scores=emotion_scores,
        crisis_score=round(crisis_score, 4),
        crisis_tier=crisis_tier,
        intent=intent,
        mhi=int(mhi),
        category=category,
    )


# -- POST /voice/transcribe ----------------------------------------------------

@app.post("/voice/transcribe", summary="Multilingual STT — audio + language detection")
async def voice_transcribe(
    audio: UploadFile = File(...),
    language: str | None = Form(None),
    user_id: ObjectId = Depends(get_current_user),
):
    """
    One Whisper pass: detects spoken language AND transcribes simultaneously.

    Response (always HTTP 200 unless the upload itself is broken):
        {
            "transcript":    "मुझे बहुत बुरा लग रहा है",
            "language_code": "hi",
            "language_name": "Hindi",
            "confidence":    0.97
        }

    transcript="" means silence — still returns 200 so the JS voice loop
    can show "No speech detected" without crashing.
    """
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file.")

    content_type = (audio.content_type or "").lower()
    if "ogg"  in content_type:                            fmt = "ogg"
    elif "mp4" in content_type or "m4a" in content_type: fmt = "mp4"
    elif "wav" in content_type:                           fmt = "wav"
    else:                                                 fmt = "webm"

    logger.debug("STT | %d bytes | fmt=%s | user=%s", len(audio_bytes), fmt, user_id)

    try:
        result = await _run_in_thread(voice_service.transcribe, audio_bytes, fmt, language)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    logger.info(
        "STT | lang=%s(%.0f%%) | text=%r",
        result.language_code, result.confidence * 100, result.text[:60],
    )
    return {
        "transcript":    result.text or "",
        "language_code": result.language_code,
        "language_name": result.language_name,
        "confidence":    result.confidence,
    }


# -- POST /voice/speak ---------------------------------------------------------

@app.post("/voice/speak", summary="Multilingual TTS — text to speech with Indian accent")
async def voice_speak(
    body: SpeakRequest,
    user_id: ObjectId = Depends(get_current_user),
):
    """
    Produces speech in body.language_code with Indian accent.
    Speed adapts to emotion_label and crisis_tier.
    Returns MP3 (gTTS) or WAV (pyttsx3 fallback).
    """
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Empty text provided.")

    logger.debug(
        "TTS | lang=%s | emotion=%s | tier=%s | text=%r",
        body.language_code, body.emotion_label, body.crisis_tier, body.text[:60],
    )

    try:
        audio_bytes = await _run_in_thread(
            voice_service.synthesize,
            body.text,
            body.language_code,
            body.emotion_label,
            body.crisis_tier,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    media_type = (
        "audio/wav" if voice_service.tts_backend == "pyttsx3" else "audio/mpeg"
    )

    return Response(
        content=audio_bytes,
        media_type=media_type,
        headers={"Cache-Control": "no-cache"},
    )


#  POST /assessment 

@app.post("/assessment", summary="Submit PHQ-2 / GAD-2 screening scores")
async def submit_assessment(
    body: AssessmentRequest,
    user_id: ObjectId = Depends(get_current_user),
):
    phq2 = max(0, min(body.phq2, 6))
    gad2 = max(0, min(body.gad2, 6))

    await db.users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "phq2_total":            phq2,
                "gad2_total":            gad2,
                "assessment_updated_at": datetime.utcnow(),
            }
        },
        upsert=False,
    )

    screening_score = screening_service.compute(phq2, gad2)
    flags           = screening_service.get_flags(phq2, gad2)

    return {
        "status":          "ok",
        "phq2":            phq2,
        "gad2":            gad2,
        "screening_score": screening_score,
        **flags,
    }


#  GET /user/history 

@app.get("/user/history", summary="Paginated conversation history")
async def user_history(
    limit: int = Query(default=10, ge=1, le=100),
    user_id: ObjectId = Depends(get_current_user),
):
    cursor = (
        db.conversations
        .find({"user_id": user_id})
        .sort("timestamp", 1)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    for d in docs:
        d.pop("_id", None)
    return {"count": len(docs), "conversations": docs}


#  GET /user/timeline

@app.get("/user/timeline", summary="MHI timeline for dashboard chart")
async def user_timeline(
    limit: int = Query(default=30, ge=1, le=100),
    user_id: ObjectId = Depends(get_current_user),
):
    cursor = (
        db.conversations
        .find(
            {"user_id": user_id},
            {"timestamp": 1, "mhi": 1, "category": 1, "crisis_tier": 1, "_id": 0},
        )
        .sort("timestamp", 1)
        .limit(limit)
    )
    return await cursor.to_list(length=limit)