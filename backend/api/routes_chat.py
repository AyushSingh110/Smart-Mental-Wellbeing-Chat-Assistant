from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime

from backend.services.emotion_service import EmotionService
from backend.services.crisis_service import CrisisService
from backend.services.intent_service import IntentService
from backend.services.matrix_service import MentalHealthMatrix
from backend.services.rag_service import RAGService
from backend.services.safety_service import SafetyService
from backend.database.mongo_client import MongoClient
from backend.dependencies import get_db

router = APIRouter(prefix="/chat", tags=["Chat"])

emotion_service = EmotionService()
crisis_service = CrisisService()
intent_service = IntentService()
matrix_service = MentalHealthMatrix()
rag_service = RAGService()
safety_service = SafetyService()


class ChatRequest(BaseModel):
    user_id: str
    message: str


@router.post("")
async def chat_endpoint(request: ChatRequest, db: MongoClient = Depends(get_db)):

    user_message = request.message

    # Emotion
    emotion_probs = emotion_service.predict(user_message)
    emotion_label = max(emotion_probs, key=emotion_probs.get)
    emotion_score = emotion_probs[emotion_label]

    # Crisis
    crisis_score = crisis_service.predict(user_message)

    # Intent
    intent = intent_service.predict(user_message)

    # Matrix
    mhi = matrix_service.compute(
        emotion_score=emotion_score,
        crisis_score=crisis_score
    )

    category = matrix_service.categorize(mhi, crisis_score)

    # RAG + LLM
    llm_response = rag_service.generate_response(
        user_message=user_message,
        emotion_label=emotion_label,
        emotion_score=emotion_score,
        intent=intent,
        mental_health_index=mhi,
        crisis_probability=crisis_score
    )

    final_response = safety_service.validate_response(
        response=llm_response,
        crisis_score=crisis_score
    )

    # Persist conversation
    conversation_doc = {
        "user_id": request.user_id,
        "message": user_message,
        "response": final_response,
        "emotion": {
            "label": emotion_label,
            "score": emotion_score
        },
        "intent": intent,
        "crisis_score": crisis_score,
        "matrix": {
            "mhi": mhi,
            "category": category
        },
        "timestamp": datetime.utcnow()
    }

    await db.store_conversation(conversation_doc)
    await db.update_latest_mhi(request.user_id, mhi)

    return {
        "response": final_response,
        "emotion": emotion_label,
        "crisis_score": crisis_score,
        "mhi": mhi,
        "category": category
    }