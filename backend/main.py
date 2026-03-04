"""
main.py — Smart Mental Well-Being Assistant · FastAPI Backend

Changes in this version:
  - Crisis early-exit: active/passive tiers skip RAG entirely
  - raw_text passed to matrix_service for hopeless-language penalty
  - category computed BEFORE RAG so length instruction is correct
  - rag_service.generate_response() now returns (response, llm_failed) tuple
  - safety_service.validate_response() takes category + llm_failed params
  - Safe fallback guaranteed — user never sees a technical error message
  - _persist() helper to avoid code duplication across early-exit paths
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from functools import partial

from fastapi import FastAPI, Query, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from backend.auth.auth_router import router as auth_router
from backend.config import settings
from backend.dependencies import get_current_user
from backend.routes.routes_report import router as report_router

from backend.services.emotion_service    import EmotionService
from backend.services.crisis_service     import CrisisService
from backend.services.intent_service     import IntentService
from backend.services.matrix_service     import MentalHealthMatrix
from backend.services.rag_service        import RAGService
from backend.services.safety_service     import SafetyService
from backend.services.behavioral_service import BehavioralService
from backend.services.screening_service  import ScreeningService
from backend.services.history_service    import HistoryService
from backend.services.voice_service      import VoiceService


# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ── MongoDB ───────────────────────────────────────────────────────────────────

mongo = AsyncIOMotorClient(
    settings.MONGO_URI,
    tls=True,
    serverSelectionTimeoutMS=5000,
)
db                = mongo[settings.MONGO_DB_NAME]
conversations_col = db["conversations"]
users_col         = db["users"]


# ── Services ──────────────────────────────────────────────────────────────────

emotion_service    = EmotionService()
crisis_service     = CrisisService()
intent_service     = IntentService()
matrix_service     = MentalHealthMatrix()
rag_service        = RAGService()
safety_service     = SafetyService()
behavioral_service = BehavioralService()
screening_service  = ScreeningService()
history_service    = HistoryService(conversations_col)
voice_service      = VoiceService()


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    emotion_scores: dict
    crisis_score: float
    crisis_tier: str       # 'active' | 'passive' | 'distress' | 'none'
    intent: str
    mhi: int
    category: str


class AssessmentRequest(BaseModel):
    phq2: int
    gad2: int


class SpeakRequest(BaseModel):
    text: str
    emotion_label: str = "default"
    crisis_tier: str   = "none"


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s …", settings.APP_NAME, settings.APP_VERSION)
    await conversations_col.create_index([("user_id", 1), ("timestamp", -1)])
    await users_col.create_index("email", unique=True)
    logger.info("MongoDB connected — database: %s", settings.MONGO_DB_NAME)
    yield
    mongo.close()
    logger.info("Shutdown complete.")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Mental health chat API with emotion/crisis detection, "
        "MHI scoring, CBT-guided LLM responses, and voice support."
    ),
    lifespan=lifespan,
)

app.include_router(report_router)
app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Thread-pool helper ────────────────────────────────────────────────────────

async def _run_in_thread(fn, *args, **kwargs):
    """Offloads CPU/IO-bound synchronous work to the thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(fn, *args, **kwargs))


# ── DB persistence helper ─────────────────────────────────────────────────────

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
    """Saves one conversation turn to MongoDB."""
    await conversations_col.insert_one({
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


# ── Routes ────────────────────────────────────────────────────────────────────

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


# ── POST /chat ────────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse, summary="Full chat pipeline")
async def chat(
    body: ChatRequest,
    user_id: ObjectId = Depends(get_current_user),
):
    # ── Step 1: ML inference — all heavy calls offloaded to thread pool ───────
    emotion_scores   = await _run_in_thread(emotion_service.predict, body.message)
    emotion_label    = max(emotion_scores, key=emotion_scores.get)
    emotion_score    = emotion_scores[emotion_label]

    crisis_score     = await _run_in_thread(crisis_service.predict,       body.message)
    crisis_tier      = await _run_in_thread(crisis_service.classify_tier, body.message)

    intent           = await _run_in_thread(intent_service.predict, body.message)
    behavioral_score = behavioral_service.predict(body.message)   # regex — fast

    logger.debug(
        "msg=%r | emotion=%s(%.2f) | crisis=%.3f | tier=%s | behavioral=%.2f",
        body.message[:60], emotion_label, emotion_score,
        crisis_score, crisis_tier, behavioral_score,
    )

    # ── Step 2: DB-dependent scoring ──────────────────────────────────────────
    history_score = await history_service.compute(user_id)

    user_doc = await users_col.find_one(
        {"_id": user_id},
        {"phq2_total": 1, "gad2_total": 1},
    )
    phq2 = int(user_doc.get("phq2_total", 0)) if user_doc else 0
    gad2 = int(user_doc.get("gad2_total", 0)) if user_doc else 0
    screening_score = screening_service.compute(phq2, gad2)

    # ── Step 3: MHI — raw_text enables hopeless-language penalty ─────────────
    mhi = matrix_service.compute(
        emotion_score    = emotion_score,
        crisis_score     = crisis_score,
        emotion_label    = emotion_label,
        screening_score  = screening_score,
        behavioral_score = behavioral_score,
        history_score    = history_score,
        crisis_tier      = crisis_tier,
        raw_text         = body.message,   # ← new: hopeless-phrase penalty
    )
    category = matrix_service.categorize(mhi, crisis_score, crisis_tier)

    logger.debug("mhi=%d | category=%s | screening=%.2f | history=%.2f",
                 mhi, category, screening_score, history_score)

    # ── Step 4: Crisis early-exit — skip RAG for active / passive ─────────────
    # safety_service returns a predefined template; LLM is never called.
    # This fixes the issue where the LLM was generating a response even for
    # active suicidal language, and safety_service had to override it anyway.

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
            response       = final_response,
            emotion_scores = emotion_scores,
            crisis_score   = round(crisis_score, 4),
            crisis_tier    = crisis_tier,
            intent         = intent,
            mhi            = int(mhi),
            category       = category,
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
            response       = final_response,
            emotion_scores = emotion_scores,
            crisis_score   = round(crisis_score, 4),
            crisis_tier    = crisis_tier,
            intent         = intent,
            mhi            = int(mhi),
            category       = category,
        )

    # ── Step 5: RAG response ──────────────────────────────────────────────────
    # category is already known → RAG builds a length-aware prompt.
    # generate_response() returns (text, llm_failed_bool).
    llm_response, llm_failed = await _run_in_thread(
        rag_service.generate_response,
        body.message,
        emotion_label,
        emotion_score,
        intent,
        mhi,
        crisis_score,
        crisis_tier,
        category,       # ← new: correct length instruction in prompt
    )

    # ── Step 6: Safety validation + length trim ───────────────────────────────
    final_response = safety_service.validate_response(
        response     = llm_response,
        crisis_score = crisis_score,
        crisis_tier  = crisis_tier,
        category     = category,     # ← new: drives sentence-limit trim
        llm_failed   = llm_failed,   # ← new: triggers warm fallback if True
    )

    # ── Step 7: Persist to MongoDB ────────────────────────────────────────────
    await _persist(
        user_id, body.message, emotion_scores, crisis_score, crisis_tier,
        behavioral_score, screening_score, history_score, intent, mhi, category,
    )

    return ChatResponse(
        response       = final_response,
        emotion_scores = emotion_scores,
        crisis_score   = round(crisis_score, 4),
        crisis_tier    = crisis_tier,
        intent         = intent,
        mhi            = int(mhi),
        category       = category,
    )


# ── POST /voice/transcribe ────────────────────────────────────────────────────

@app.post("/voice/transcribe", summary="STT — Audio → transcript")
async def voice_transcribe(
    audio: UploadFile = File(...),
    user_id: ObjectId = Depends(get_current_user),
):
    """
    Accepts audio recorded by the browser (WebM / OGG / WAV / MP4).
    Returns {"transcript": "..."} with HTTP 200 in all non-error cases.

    Return values:
        {"transcript": "hello world"}  — speech detected
        {"transcript": ""}             — silence / too quiet (NOT an error)

    HTTP errors:
        400  — file upload contained zero bytes
        503  — STT backend not installed
    """
    audio_bytes = await audio.read()

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file — no bytes received.")

    content_type = (audio.content_type or "").lower()
    if "ogg"  in content_type:               fmt = "ogg"
    elif "mp4" in content_type or "m4a" in content_type: fmt = "mp4"
    elif "wav" in content_type:              fmt = "wav"
    else:                                    fmt = "webm"

    logger.debug("STT | %d bytes | fmt=%s | mime=%s | user=%s",
                 len(audio_bytes), fmt, content_type, user_id)

    try:
        transcript = await _run_in_thread(voice_service.transcribe, audio_bytes, fmt)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    result = transcript or ""
    logger.debug("STT result: %r", result[:80] if result else "(silent)")
    return {"transcript": result}


# ── POST /voice/speak ─────────────────────────────────────────────────────────

@app.post("/voice/speak", summary="TTS — Text → audio bytes")
async def voice_speak(
    body: SpeakRequest,
    user_id: ObjectId = Depends(get_current_user),
):
    """
    Returns raw audio bytes (WAV for pyttsx3, MP3 for gTTS).
    Voice profile adapts to emotion_label and crisis_tier.
    """
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Empty text provided.")

    logger.debug("TTS | emotion=%s | tier=%s | text=%r",
                 body.emotion_label, body.crisis_tier, body.text[:60])

    try:
        audio_bytes = await _run_in_thread(
            voice_service.synthesize,
            body.text,
            body.emotion_label,
            body.crisis_tier,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    media_type = (
        "audio/wav" if voice_service._tts_backend == "pyttsx3" else "audio/mpeg"
    )
    return Response(
        content=audio_bytes,
        media_type=media_type,
        headers={"Cache-Control": "no-cache"},
    )


# ── POST /assessment ──────────────────────────────────────────────────────────

@app.post("/assessment", summary="Submit PHQ-2 / GAD-2 screening scores")
async def submit_assessment(
    body: AssessmentRequest,
    user_id: ObjectId = Depends(get_current_user),
):
    phq2 = max(0, min(body.phq2, 6))
    gad2 = max(0, min(body.gad2, 6))

    await users_col.update_one(
        {"_id": user_id},
        {"$set": {
            "phq2_total":            phq2,
            "gad2_total":            gad2,
            "assessment_updated_at": datetime.utcnow(),
        }},
        upsert=False,
    )

    return {
        "status":          "ok",
        "phq2":            phq2,
        "gad2":            gad2,
        "screening_score": screening_service.compute(phq2, gad2),
        **screening_service.get_flags(phq2, gad2),
    }


# ── GET /user/history ─────────────────────────────────────────────────────────

@app.get("/user/history", summary="Paginated conversation history")
async def user_history(
    limit: int = Query(default=10, ge=1, le=100),
    user_id: ObjectId = Depends(get_current_user),
):
    cursor = (
        conversations_col
        .find({"user_id": user_id})
        .sort("timestamp", 1)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    for d in docs:
        d.pop("_id", None)
    return {"count": len(docs), "conversations": docs}


# ── GET /user/timeline ────────────────────────────────────────────────────────

@app.get("/user/timeline", summary="MHI timeline for dashboard chart")
async def user_timeline(
    limit: int = Query(default=30, ge=1, le=100),
    user_id: ObjectId = Depends(get_current_user),
):
    cursor = (
        conversations_col
        .find(
            {"user_id": user_id},
            {"timestamp": 1, "mhi": 1, "category": 1, "crisis_tier": 1, "_id": 0},
        )
        .sort("timestamp", 1)
        .limit(limit)
    )
    return await cursor.to_list(length=limit)