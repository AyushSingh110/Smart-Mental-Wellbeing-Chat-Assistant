from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from backend.auth.auth_router import router as auth_router
from backend.config import settings
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


logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

mongo = AsyncIOMotorClient(
    settings.MONGO_URI,
    tls=True,
    serverSelectionTimeoutMS=5000,
)

db = mongo[settings.MONGO_DB_NAME]
conversations_col = db["conversations"]
users_col = db["users"]

# Stateless services — instantiated once at startup
emotion_service   = EmotionService()
crisis_service    = CrisisService()
intent_service    = IntentService()
matrix_service    = MentalHealthMatrix()
rag_service       = RAGService()
safety_service    = SafetyService()
behavioral_service = BehavioralService()
screening_service  = ScreeningService()

# HistoryService requires a DB collection reference
history_service = HistoryService(conversations_col)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    emotion_scores: dict
    crisis_score: float
    intent: str
    mhi: int
    category: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s …", settings.APP_NAME, settings.APP_VERSION)
    await conversations_col.create_index([("user_id", 1), ("timestamp", -1)])
    await users_col.create_index("email", unique=True)
    logger.info("MongoDB connected – database: %s", settings.MONGO_DB_NAME)
    yield
    mongo.close()
    logger.info("Shutdown complete.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Mental health chat API with emotion/crisis detection and MHI scoring.",
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


@app.get("/", summary="Root – API info")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "endpoints": {
            "POST /chat": "Send a message through the analysis pipeline",
            "GET /user/history": "Conversation history",
            "GET /user/timeline": "MHI timeline for charts",
        },
    }


@app.post("/chat", response_model=ChatResponse, summary="Chat pipeline")
async def chat(
    body: ChatRequest,
    user_id: ObjectId = Depends(get_current_user),
):
    # ── ML inference (synchronous, CPU-bound) ────────────────────────────────
    emotion_scores  = emotion_service.predict(body.message)
    emotion_label   = max(emotion_scores, key=emotion_scores.get)
    emotion_score   = emotion_scores[emotion_label]

    crisis_score    = crisis_service.predict(body.message)
    intent          = intent_service.predict(body.message)
    behavioral_score = behavioral_service.predict(body.message)

    # ── Async DB-dependent scoring ────────────────────────────────────────────
    history_score = await history_service.compute(user_id)

    # ── Screening score: pulled from user profile if available ───────────────
    # Defaults to 0.0 (no assessment submitted) — updated via /assessment route
    user_doc = await users_col.find_one(
        {"_id": user_id},
        {"phq2_total": 1, "gad2_total": 1}
    )
    phq2 = int(user_doc.get("phq2_total", 0)) if user_doc else 0
    gad2 = int(user_doc.get("gad2_total", 0)) if user_doc else 0
    screening_score = screening_service.compute(phq2, gad2)

    # ── MHI computation ───────────────────────────────────────────────────────
    mhi = matrix_service.compute(
        emotion_score=emotion_score,
        crisis_score=crisis_score,
        emotion_label=emotion_label,
        screening_score=screening_score,
        behavioral_score=behavioral_score,
        history_score=history_score,
    )
    category = matrix_service.categorize(mhi, crisis_score)

    # ── LLM response generation ───────────────────────────────────────────────
    llm_response = rag_service.generate_response(
        user_message=body.message,
        emotion_label=emotion_label,
        emotion_score=emotion_score,
        intent=intent,
        mental_health_index=mhi,
        crisis_probability=crisis_score,
    )

    final_response = safety_service.validate_response(
        response=llm_response,
        crisis_score=crisis_score,
    )

    # ── Persist conversation ──────────────────────────────────────────────────
    await conversations_col.insert_one({
        "user_id":          user_id,
        "timestamp":        datetime.utcnow(),
        "message":          body.message,
        "emotion_scores":   emotion_scores,
        "crisis_score":     round(crisis_score, 4),
        "behavioral_score": round(behavioral_score, 4),
        "screening_score":  round(screening_score, 4),
        "history_score":    round(history_score, 4),
        "intent":           intent,
        "mhi":              int(mhi),
        "category":         category,
    })

    return ChatResponse(
        response=final_response,
        emotion_scores=emotion_scores,
        crisis_score=round(crisis_score, 4),
        intent=intent,
        mhi=int(mhi),
        category=category,
    )


@app.post("/assessment", summary="Submit PHQ-2 / GAD-2 assessment scores")
async def submit_assessment(
    phq2: int,
    gad2: int,
    user_id: ObjectId = Depends(get_current_user),
):
    """
    Stores the latest PHQ-2 and GAD-2 totals on the user document.
    These are picked up by the /chat route to compute screening_score.
    """
    phq2 = max(0, min(phq2, 6))
    gad2 = max(0, min(gad2, 6))

    await users_col.update_one(
        {"_id": user_id},
        {"$set": {
            "phq2_total": phq2,
            "gad2_total": gad2,
            "assessment_updated_at": datetime.utcnow(),
        }},
        upsert=False,
    )
    return {"status": "ok", "phq2": phq2, "gad2": gad2}


@app.get("/user/history", summary="Conversation history")
async def user_history(
    limit: int = Query(default=10, ge=1, le=100),
    user_id: ObjectId = Depends(get_current_user),
):
    cursor = (
        conversations_col.find({"user_id": user_id})
        .sort("timestamp", 1)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    for d in docs:
        d.pop("_id", None)

    return {"count": len(docs), "conversations": docs}


@app.get("/user/timeline", summary="MHI timeline for trend chart")
async def user_timeline(
    limit: int = Query(default=30, ge=1, le=100),
    user_id: ObjectId = Depends(get_current_user),
):
    cursor = (
        conversations_col.find(
            {"user_id": user_id},
            {"timestamp": 1, "mhi": 1, "category": 1, "_id": 0}
        )
        .sort("timestamp", 1)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    return docs
