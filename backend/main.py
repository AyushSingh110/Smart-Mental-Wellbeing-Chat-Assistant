from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient

from backend.config import settings
from backend.services.emotion_service import EmotionService
from backend.services.crisis_service import CrisisService
from backend.services.intent_service import IntentService
from backend.services.matrix_service import MentalHealthMatrix
from backend.services.rag_service import RAGService
from backend.services.safety_service import SafetyService
from backend.routes.routes_report import router as report_router



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

emotion_service = EmotionService()
crisis_service = CrisisService()
intent_service = IntentService()
matrix_service = MentalHealthMatrix()
rag_service = RAGService()
safety_service = SafetyService()


class ChatRequest(BaseModel):
    user_id: str
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

    # Create indexes asynchronously
    await conversations_col.create_index([("user_id", 1), ("timestamp", -1)])
    await users_col.create_index("user_id", unique=True)

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
            "GET /user/{user_id}/history": "Conversation history",
            "GET /user/{user_id}/timeline": "MHI timeline for charts",
        },
    }


@app.post("/chat", response_model=ChatResponse, summary="Chat pipeline")
async def chat(body: ChatRequest):
    existing = await users_col.find_one({"user_id": body.user_id})
    if not existing:
        await users_col.insert_one({
            "user_id": body.user_id,
            "created_at": datetime.utcnow(),
            "baseline_mhi": 78,
        })

    emotion_scores = emotion_service.predict(body.message)
    emotion_label = max(emotion_scores, key=emotion_scores.get)

    crisis_score = crisis_service.predict(body.message)

    intent = intent_service.predict(body.message)

    mhi = matrix_service.compute(
        emotion_score=emotion_scores[emotion_label],
        crisis_score=crisis_score,
    )
    category = matrix_service.categorize(mhi, crisis_score)

    llm_response = rag_service.generate_response(
        user_message=body.message,
        emotion_label=emotion_label,
        emotion_score=emotion_scores[emotion_label],
        intent=intent,
        mental_health_index=mhi,
        crisis_probability=crisis_score,
    )

    final_response = safety_service.validate_response(
        response=llm_response,
        crisis_score=crisis_score,
    )

    await conversations_col.insert_one({
        "user_id": body.user_id,
        "timestamp": datetime.utcnow(),
        "message": body.message,
        "emotion_scores": emotion_scores,
        "crisis_score": round(crisis_score, 4),
        "intent": intent,
        "mhi": int(mhi),
        "category": category,
    })

    return ChatResponse(
        response=final_response,
        emotion_scores=emotion_scores,
        crisis_score=round(crisis_score, 4),
        intent=intent,
        mhi=int(mhi),
        category=category,
    )




@app.get("/user/{user_id}/history", summary="Conversation history")
async def user_history(user_id: str, limit: int = Query(default=10, ge=1, le=100)):

    cursor = (
        conversations_col.find({"user_id": user_id})
        .sort("timestamp", 1)
        .limit(limit)
    )

    docs = await cursor.to_list(length=limit)

    for d in docs:
        d.pop("_id", None)

    return {
        "user_id": user_id,
        "count": len(docs),
        "conversations": docs,
    }
