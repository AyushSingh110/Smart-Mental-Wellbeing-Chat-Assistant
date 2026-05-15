from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from functools import partial

from fastapi import FastAPI, Query, Depends, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from bson import ObjectId

from backend.auth.auth_router import router as auth_router
from backend.config import settings
from backend.database.mongo_client import db
from backend.database.schemas import (
    AvatarSpeakRequest,
    CBTSessionCreate,
    ChatRequest,
    ChatResponse,
    AssessmentRequest,
    MoodJournalEntry,
    SpeakRequest,
    UserProfileUpdate,
)
from backend.dependencies import get_current_user

try:
    from backend.routes.routes_report import router as report_router
except Exception as exc:  # pragma: no cover - depends on optional libs
    report_router = None

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
from backend.services.musetalk_service import MuseTalkService


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
musetalk_service   = MuseTalkService()


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
    "http://localhost:5173",
    "http://127.0.0.1:5173",
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
if report_router is not None:
    app.include_router(report_router)
else:
    logger.warning("Report routes disabled because optional report dependencies are unavailable")


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
    response: str,
    emotion_scores: dict,
    crisis_score: float,
    crisis_tier: str,
    behavioral_score: float,
    screening_score: float,
    history_score: float,
    intent: str,
    mhi: float,
    category: str,
    language_code: str,
    source: str = "text",
    cbt_technique_suggested: str | None = None,
) -> None:
    """Saves one conversation turn to MongoDB. Used by all /chat exit paths."""
    doc = {
        "user_id":          user_id,
        "timestamp":        datetime.utcnow(),
        "message":          message,
        "response":         response,
        "emotion_scores":   emotion_scores,
        "crisis_score":     round(crisis_score, 4),
        "crisis_tier":      crisis_tier,
        "behavioral_score": round(behavioral_score, 4),
        "screening_score":  round(screening_score, 4),
        "history_score":    round(history_score, 4),
        "intent":           intent,
        "mhi":              int(mhi),
        "category":         category,
        "language_code":    language_code,
        "source":           source,
    }
    if cbt_technique_suggested:
        doc["cbt_technique_suggested"] = cbt_technique_suggested
    await db.conversations.insert_one(doc)
    await db.update_latest_mhi(user_id, int(mhi))


# -- CBT technique suggestion helper ------------------------------------------

_CBT_SUGGESTIONS: dict[str, str] = {
    "Moderate Distress":  "thought_record",
    "High Risk":          "breathing",
    "Depression Risk":    "mood_journal",
    "Crisis Risk":        "grounding",
}

def _suggest_cbt(category: str, crisis_tier: str) -> str | None:
    if crisis_tier in ("active", "passive"):
        return "grounding"
    return _CBT_SUGGESTIONS.get(category)


# -- Crisis event logger -------------------------------------------------------

async def _log_crisis_event(
    user_id,
    crisis_tier: str,
    crisis_score: float,
    message_snippet: str,
) -> None:
    if crisis_tier in ("active", "passive", "distress"):
        try:
            await db.db["crisis_events"].insert_one({
                "user_id":        user_id,
                "timestamp":      datetime.utcnow(),
                "crisis_tier":    crisis_tier,
                "crisis_score":   round(crisis_score, 4),
                "message_snippet": message_snippet[:120],
            })
        except Exception as exc:
            logger.warning("Could not log crisis event: %s", exc)



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


@app.get("/health", summary="Health check", tags=["Ops"])
async def health():
    """Liveness probe used by load balancers and deployment pipelines."""
    db_ok = False
    try:
        await db.db.command("ping")
        db_ok = True
    except Exception:
        pass
    return {
        "status":  "ok" if db_ok else "degraded",
        "version": settings.APP_VERSION,
        "db":      "connected" if db_ok else "unreachable",
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
    user_id_str = str(user_id)

    # Step 1: ML inference — offloaded to thread pool
    (
        emotion_full,
        intent,
        history_score,
        history_snapshot,
    ) = await asyncio.gather(
        _run_in_thread(emotion_service.predict_full, body.message),
        _run_in_thread(intent_service.predict, body.message),
        history_service.compute(user_id),
        history_service.get_recent_snapshot(user_id),
    )

    # Extract emotion fields
    emotion_scores       = emotion_full.scores
    emotion_label        = emotion_full.top_label
    emotion_score        = emotion_full.top_score
    emotion_complexity   = emotion_full.emotion_complexity
    suppression_flagged  = emotion_full.suppression_flagged
    top_3_emotions       = emotion_full.top_3

    # Step 2: Crisis detection with temporal escalation + velocity
    crisis_tier, crisis_score = await _run_in_thread(
        crisis_service.classify_tier_with_history, body.message, user_id_str
    )
    crisis_velocity = crisis_service.get_crisis_velocity(user_id_str)

    # Step 3: Behavioral profile (pure regex — fast, no thread needed)
    behavioral_profile_obj = behavioral_service.predict_profile(body.message)
    behavioral_score       = behavioral_profile_obj.overall_score

    logger.debug(
        "msg=%r | emotion=%s(%.2f) complex=%.3f | crisis=%.3f tier=%s vel=%.3f | behavioral=%.3f",
        body.message[:60], emotion_label, emotion_score, emotion_complexity,
        crisis_score, crisis_tier, crisis_velocity, behavioral_score,
    )

    # Step 4: Screening scores from DB
    user_doc = await db.users.find_one(
        {"_id": user_id},
        {"phq2_total": 1, "gad2_total": 1},
    )
    phq2 = int(user_doc.get("phq2_total", 0)) if user_doc else 0
    gad2 = int(user_doc.get("gad2_total", 0)) if user_doc else 0
    screening_score = screening_service.compute(phq2, gad2)

    # Step 5: Compute MHI with enhanced inputs
    mhi_trajectory = history_snapshot.get("mhi_trajectory", "stable")
    mhi = matrix_service.compute(
        emotion_score       = emotion_score,
        crisis_score        = crisis_score,
        emotion_label       = emotion_label,
        screening_score     = screening_score,
        behavioral_score    = behavioral_score,
        history_score       = history_score,
        crisis_tier         = crisis_tier,
        raw_text            = body.message,
        recent_emotions     = history_snapshot.get("recent_emotions"),
        mhi_trend           = history_snapshot.get("recent_mhi"),
        emotion_complexity  = emotion_complexity,
        suppression_flagged = suppression_flagged,
    )
    category = matrix_service.categorize(mhi, crisis_score, crisis_tier)

    # Cross-session reference detection
    cross_session_ref = history_service.detect_cross_session_reference(body.message)

    # pre-voice alert: crisis escalating quickly or tier elevated
    pre_voice_alert = crisis_velocity > 0.30 or crisis_tier in ("passive", "active")

    logger.debug(
        "mhi=%d | category=%s | screening=%.2f | history=%.2f | trajectory=%s",
        mhi, category, screening_score, history_score, mhi_trajectory,
    )

    # Step 6: Crisis early-exit — skip RAG for active/passive tiers
    def _make_crisis_response(final_response: str, cbt_hint: str | None) -> ChatResponse:
        return ChatResponse(
            response=final_response,
            emotion_scores=emotion_scores,
            crisis_score=round(crisis_score, 4),
            crisis_tier=crisis_tier,
            intent=intent,
            mhi=int(mhi),
            category=category,
            cbt_technique_suggested=cbt_hint,
            top_3_emotions=[(lbl, scr) for lbl, scr in top_3_emotions],
            emotion_complexity=emotion_complexity,
            suppression_flagged=suppression_flagged,
            crisis_velocity=crisis_velocity,
            behavioral_profile={
                "overall": behavioral_profile_obj.overall_score,
                "categories": behavioral_profile_obj.category_scores,
                "flagged": behavioral_profile_obj.flagged_categories,
                "dominant": behavioral_profile_obj.dominant_category,
            },
            pre_voice_alert=pre_voice_alert,
            mhi_trajectory=mhi_trajectory,
        )

    if safety_service.is_active_crisis(
        crisis_tier, crisis_score, settings.SAFETY_OVERRIDE_THRESHOLD
    ):
        logger.info("ACTIVE CRISIS | tier=%s score=%.3f | RAG skipped", crisis_tier, crisis_score)
        final_response = safety_service.validate_response(
            response="", crisis_score=crisis_score, crisis_tier=crisis_tier,
            category=category, llm_failed=False,
        )
        cbt_hint = _suggest_cbt(category, crisis_tier)
        await _persist(
            user_id, body.message, final_response, emotion_scores, crisis_score, crisis_tier,
            behavioral_score, screening_score, history_score, intent, mhi, category,
            body.language_code, body.source, cbt_hint,
        )
        await _log_crisis_event(user_id, crisis_tier, crisis_score, body.message)
        return _make_crisis_response(final_response, cbt_hint)

    if safety_service.is_passive_crisis(
        crisis_tier, crisis_score, settings.CRISIS_PROBABILITY_THRESHOLD
    ):
        logger.info("PASSIVE CRISIS | tier=%s score=%.3f | RAG skipped", crisis_tier, crisis_score)
        final_response = safety_service.validate_response(
            response="", crisis_score=crisis_score, crisis_tier=crisis_tier,
            category=category, llm_failed=False,
        )
        cbt_hint = _suggest_cbt(category, crisis_tier)
        await _persist(
            user_id, body.message, final_response, emotion_scores, crisis_score, crisis_tier,
            behavioral_score, screening_score, history_score, intent, mhi, category,
            body.language_code, body.source, cbt_hint,
        )
        await _log_crisis_event(user_id, crisis_tier, crisis_score, body.message)
        return _make_crisis_response(final_response, cbt_hint)

    # Step 7: RAG-augmented LLM response with enhanced context
    cbt_hint = _suggest_cbt(category, crisis_tier)
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
        history_snapshot.get("conversation_pairs"),
        cbt_hint,
        cross_session_ref,
        crisis_velocity,
        mhi_trajectory,
    )

    # Step 8: Safety validation + length trim
    final_response = safety_service.validate_response(
        response=llm_response, crisis_score=crisis_score, crisis_tier=crisis_tier,
        category=category, llm_failed=llm_failed,
    )

    # Step 9: Persist to MongoDB
    await _persist(
        user_id, body.message, final_response, emotion_scores, crisis_score, crisis_tier,
        behavioral_score, screening_score, history_score, intent, mhi, category,
        body.language_code, body.source, cbt_hint,
    )
    if crisis_tier == "distress":
        await _log_crisis_event(user_id, crisis_tier, crisis_score, body.message)

    return ChatResponse(
        response=final_response,
        emotion_scores=emotion_scores,
        crisis_score=round(crisis_score, 4),
        crisis_tier=crisis_tier,
        intent=intent,
        mhi=int(mhi),
        category=category,
        cbt_technique_suggested=cbt_hint,
        top_3_emotions=[(lbl, scr) for lbl, scr in top_3_emotions],
        emotion_complexity=emotion_complexity,
        suppression_flagged=suppression_flagged,
        crisis_velocity=crisis_velocity,
        behavioral_profile={
            "overall": behavioral_profile_obj.overall_score,
            "categories": behavioral_profile_obj.category_scores,
            "flagged": behavioral_profile_obj.flagged_categories,
            "dominant": behavioral_profile_obj.dominant_category,
        },
        pre_voice_alert=pre_voice_alert,
        mhi_trajectory=mhi_trajectory,
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

    # Feature 3: If Whisper confidence < 0.75, fall back to user's preferred_language
    effective_lang = result.language_code
    if result.confidence < 0.75:
        user_doc = await db.users.find_one({"_id": user_id}, {"preferred_language": 1})
        preferred = (user_doc or {}).get("preferred_language", "en")
        if preferred and preferred != result.language_code:
            logger.info(
                "STT low confidence (%.2f) — using preferred_language=%s instead of detected=%s",
                result.confidence, preferred, result.language_code,
            )
            effective_lang = preferred

    logger.info(
        "STT | lang=%s(%.0f%%) effective=%s | text=%r",
        result.language_code, result.confidence * 100, effective_lang, result.text[:60],
    )
    return {
        "transcript":    result.text or "",
        "language_code": effective_lang,
        "language_name": result.language_name,
        "confidence":    result.confidence,
        "detected_lang": result.language_code,
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
        d.pop("user_id", None)
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
            {
                "timestamp": 1,
                "mhi": 1,
                "category": 1,
                "crisis_tier": 1,
                "language_code": 1,
                "source": 1,
                "_id": 0,
            },
        )
        .sort("timestamp", 1)
        .limit(limit)
    )
    return await cursor.to_list(length=limit)


@app.get("/user/dashboard-summary", summary="Authenticated dashboard summary")
async def user_dashboard_summary(
    user_id: ObjectId = Depends(get_current_user),
):
    user = await db.users.find_one({"_id": user_id}) or {}
    recent = await db.get_recent_conversations(user_id, limit=7)

    def _ts(item) -> datetime:
        ts = item.get("timestamp")
        if isinstance(ts, datetime):
            return ts.replace(tzinfo=None) if ts.tzinfo else ts
        return datetime.utcnow()

    recent_sorted = sorted(recent, key=_ts)

    latest_mhi = int(
        (recent_sorted[-1].get("mhi") if recent_sorted else None)
        or user.get("latest_mhi")
        or user.get("baseline_mhi", 75)
    )
    category = (
        recent_sorted[-1].get("category")
        if recent_sorted
        else matrix_service.categorize(latest_mhi, 0.0, "none")
    )
    weekly_trend = [int(entry.get("mhi", latest_mhi)) for entry in recent_sorted][-7:]
    if not weekly_trend:
        weekly_trend = [latest_mhi]

    emotion_totals: dict[str, float] = {}
    for entry in recent_sorted:
        for label, value in (entry.get("emotion_scores") or {}).items():
            emotion_totals[label] = emotion_totals.get(label, 0.0) + float(value)

    if emotion_totals:
        total = sum(emotion_totals.values()) or 1.0
        emotion_mix = [
            {"label": label.replace("_", " ").title(), "value": round((score / total) * 100)}
            for label, score in sorted(emotion_totals.items(), key=lambda item: item[1], reverse=True)[:5]
        ]
    else:
        emotion_mix = [{"label": "Neutral", "value": 100}]

    recent_sessions = []
    for index, entry in enumerate(reversed(recent_sorted[-5:]), start=1):
        scores = entry.get("emotion_scores") or {"neutral": 1}
        top_emotion = max(scores, key=scores.get) if scores else "neutral"
        recent_sessions.append(
            {
                "id": str(index),
                "time": _ts(entry).isoformat(),
                "summary": (entry.get("message") or "")[:140] or "Well-being check-in",
                "mood": top_emotion,
                "mhi": int(entry.get("mhi", latest_mhi)),
            }
        )

    # CBT sessions for current user
    cbt_cursor = db.db["cbt_sessions"].find(
        {"user_id": user_id},
        {"technique": 1, "completed_at": 1, "_id": 0},
    ).sort("completed_at", -1).limit(20)
    cbt_docs = await cbt_cursor.to_list(length=20)
    cbt_counts: dict[str, int] = {}
    for c in cbt_docs:
        t = c.get("technique", "unknown")
        cbt_counts[t] = cbt_counts.get(t, 0) + 1

    # Session summary
    langs_used = list({e.get("language_code", "en") for e in recent_sorted})
    avg_mhi = round(sum(e.get("mhi", 75) for e in recent_sorted) / max(len(recent_sorted), 1))

    return {
        "displayName": user.get("name") or user.get("email", "User").split("@")[0].title(),
        "email": user.get("email", ""),
        "latestMhi": latest_mhi,
        "category": category,
        "checkInsThisWeek": len(recent_sorted),
        "streakDays": min(len(recent_sorted), 30),
        "voiceEnabled": True,
        "weeklyTrend": weekly_trend,
        "emotionMix": emotion_mix,
        "recentSessions": recent_sessions,
        "assessment": {
            "phq2": int(user.get("phq2_total", 0)),
            "gad2": int(user.get("gad2_total", 0)),
        },
        "cbtCounts": cbt_counts,
        "sessionSummary": {
            "totalTurns": len(recent_sorted),
            "avgMhi": avg_mhi,
            "languagesUsed": langs_used,
        },
        "avatarId": user.get("avatar_id", "therapist"),
        "preferredLanguage": user.get("preferred_language", "en"),
    }


# -- GET /user/profile ---------------------------------------------------------

@app.get("/user/profile", summary="Get user profile with avatar and language")
async def get_user_profile(user_id: ObjectId = Depends(get_current_user)):
    user = await db.users.find_one({"_id": user_id}) or {}
    return {
        "avatar_id":          user.get("avatar_id", "therapist"),
        "preferred_language": user.get("preferred_language", "en"),
        "name":               user.get("name", ""),
        "email":              user.get("email", ""),
        "latest_mhi":         int(user.get("latest_mhi", user.get("baseline_mhi", 75))),
    }


# -- PUT /user/profile ---------------------------------------------------------

@app.put("/user/profile", summary="Update avatar and/or preferred language")
async def update_user_profile(
    body: UserProfileUpdate,
    user_id: ObjectId = Depends(get_current_user),
):
    update_fields: dict = {}
    if body.avatar_id is not None:
        valid_avatars = {"therapist", "companion", "guide", "elder"}
        if body.avatar_id not in valid_avatars:
            raise HTTPException(status_code=400, detail=f"avatar_id must be one of {valid_avatars}")
        update_fields["avatar_id"] = body.avatar_id
    if body.preferred_language is not None:
        update_fields["preferred_language"] = body.preferred_language

    if update_fields:
        await db.users.update_one({"_id": user_id}, {"$set": update_fields})
    return {"status": "ok", **update_fields}


# -- POST /avatar/speak --------------------------------------------------------

@app.post("/avatar/speak", summary="Avatar TTS — text to speech with avatar voice")
async def avatar_speak(
    body: AvatarSpeakRequest,
    user_id: ObjectId = Depends(get_current_user),
):
    """
    Generates TTS audio with the chosen avatar's voice.
    Returns MP3 audio bytes. Uses ElevenLabs → gTTS → pyttsx3 priority chain.
    The frontend plays this audio while animating the avatar's mouth via CSS.
    """
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Empty text provided.")

    logger.debug(
        "Avatar TTS | avatar=%s lang=%s emotion=%s tier=%s text=%r",
        body.avatar_id, body.language_code, body.emotion_label, body.crisis_tier, body.text[:60],
    )

    try:
        audio_bytes = await _run_in_thread(
            voice_service.synthesize,
            body.text,
            body.language_code,
            body.emotion_label,
            body.crisis_tier,
            body.avatar_id,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    media_type = "audio/wav" if voice_service.tts_backend == "pyttsx3" else "audio/mpeg"
    # Estimate duration in ms for frontend animation sync
    # ~150 wpm → ~2.5 chars/sec; rough estimate
    estimated_duration_ms = max(1000, int(len(body.text) / 2.5 * 1000 / 60))

    return Response(
        content=audio_bytes,
        media_type=media_type,
        headers={
            "Cache-Control": "no-cache",
            "X-Audio-Duration-Ms": str(estimated_duration_ms),
        },
    )


# -- GET /voice/quota ----------------------------------------------------------

@app.get("/voice/quota", summary="ElevenLabs character quota status")
async def voice_quota(user_id: ObjectId = Depends(get_current_user)):
    """Returns approximate ElevenLabs character usage for this session."""
    return voice_service.get_elevenlabs_quota()


# -- POST /cbt/session ---------------------------------------------------------

@app.post("/cbt/session", summary="Record a CBT technique session")
async def create_cbt_session(
    body: CBTSessionCreate,
    user_id: ObjectId = Depends(get_current_user),
):
    valid = {"thought_record", "breathing", "grounding", "mood_journal", "cognitive_restructuring"}
    if body.technique not in valid:
        raise HTTPException(status_code=400, detail=f"technique must be one of {valid}")

    now = datetime.utcnow()
    doc = {
        "user_id":    user_id,
        "technique":  body.technique,
        "started_at": now,
        "notes":      body.notes,
    }
    if body.completed:
        doc["completed_at"] = now

    result = await db.db["cbt_sessions"].insert_one(doc)
    return {"status": "ok", "session_id": str(result.inserted_id)}


# -- GET /cbt/sessions ---------------------------------------------------------

@app.get("/cbt/sessions", summary="Get CBT session history")
async def get_cbt_sessions(
    limit: int = Query(default=20, ge=1, le=100),
    user_id: ObjectId = Depends(get_current_user),
):
    cursor = (
        db.db["cbt_sessions"]
        .find({"user_id": user_id})
        .sort("started_at", -1)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    for d in docs:
        d.pop("_id", None)
        d.pop("user_id", None)
        if "started_at" in d:
            d["started_at"] = d["started_at"].isoformat()
        if "completed_at" in d:
            d["completed_at"] = d["completed_at"].isoformat()
    return {"count": len(docs), "sessions": docs}


# -- POST /mood/journal --------------------------------------------------------

@app.post("/mood/journal", summary="Save a mood journal entry")
async def save_mood_entry(
    body: MoodJournalEntry,
    user_id: ObjectId = Depends(get_current_user),
):
    rating = max(1, min(10, body.mood_rating))
    await db.db["mood_journal"].insert_one({
        "user_id":     user_id,
        "timestamp":   datetime.utcnow(),
        "mood_rating": rating,
        "notes":       body.notes,
    })
    return {"status": "ok", "mood_rating": rating}


# -- GET /mood/journal ---------------------------------------------------------

@app.get("/mood/journal", summary="Get mood journal entries")
async def get_mood_journal(
    limit: int = Query(default=30, ge=1, le=100),
    user_id: ObjectId = Depends(get_current_user),
):
    cursor = (
        db.db["mood_journal"]
        .find({"user_id": user_id})
        .sort("timestamp", -1)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    for d in docs:
        d.pop("_id", None)
        d.pop("user_id", None)
        if "timestamp" in d:
            d["timestamp"] = d["timestamp"].isoformat()
    return {"count": len(docs), "entries": docs}


# -- GET /avatar/video/{job_id} -----------------------------------------------

@app.get("/avatar/video/{job_id}", summary="Poll MuseTalk lip-sync video status / stream")
async def get_avatar_video(
    job_id: str,
    user_id: ObjectId = Depends(get_current_user),
):
    """
    Returns the job status dict, or streams the video file if status==done.
    Frontend polls this endpoint after submitting a job via /avatar/speak.
    """
    status = musetalk_service.get_job_status(job_id)
    if status.get("status") == "done":
        video_path = musetalk_service.get_video_path(job_id)
        if video_path and video_path.exists():
            return FileResponse(
                str(video_path),
                media_type="video/mp4",
                headers={"Cache-Control": "no-cache"},
            )
    return status


# -- GET /crisis/history -------------------------------------------------------

@app.get("/crisis/history", summary="Crisis event timeline for dashboard")
async def crisis_history(
    limit: int = Query(default=20, ge=1, le=100),
    user_id: ObjectId = Depends(get_current_user),
):
    cursor = (
        db.db["crisis_events"]
        .find({"user_id": user_id})
        .sort("timestamp", -1)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    for d in docs:
        d.pop("_id", None)
        d.pop("user_id", None)
        if "timestamp" in d:
            d["timestamp"] = d["timestamp"].isoformat()
    return {"count": len(docs), "events": docs}
