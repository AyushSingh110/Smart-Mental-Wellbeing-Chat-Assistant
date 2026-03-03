from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from bson import ObjectId

from backend.database.mongo_client import MongoClient
from backend.dependencies import get_db, get_current_user
from backend.services.report_service import ReportService
from backend.services.history_service import HistoryService
from backend.services.llm_service import generate_llm_response

router = APIRouter(prefix="/report", tags=["Report"])
report_service = ReportService()


@router.get("/", summary="Generate and download session PDF report")
async def generate_report(
    user_id: ObjectId = Depends(get_current_user),
    db: MongoClient   = Depends(get_db),
):
    conversations = await db.get_recent_conversations(user_id, limit=50)

    if not conversations:
        return {"error": "No session data found."}

    # Build conversation text for LLM summary
    conversation_text = "\n".join(
        f"User: {c['message']}" for c in conversations
    )

    summary_prompt = f"""
You are a clinical AI assistant writing a structured session summary for a therapist.

Analyze the following mental health conversation and provide:
1. Dominant emotional patterns observed
2. Behavioral themes or risk indicators
3. Cognitive distortions identified
4. Overall mental health trajectory
5. Recommended focus areas for next session

Keep the tone professional, empathetic, and clinically grounded.
Do NOT include personal identifiers.

Conversation:
{conversation_text}
"""

    summary = generate_llm_response(summary_prompt)

    mhi_values = [c["mhi"] for c in conversations if "mhi" in c]
    avg_mhi = round(sum(mhi_values) / len(mhi_values), 2) if mhi_values else 0.0
    session_count = len(conversations)

    # Latest category and trend from history service
    latest_category = conversations[-1].get("category", "—") if conversations else "—"

    # Inline trend calculation (avoid extra DB round-trip)
    if len(mhi_values) >= 2:
        delta = mhi_values[-1] - mhi_values[0]
        trend = "improving" if delta > 5 else ("declining" if delta < -5 else "stable")
    else:
        trend = "insufficient data"

    pdf_buffer = report_service.generate_pdf(
        user_id=str(user_id),
        summary=summary,
        mhi_avg=avg_mhi,
        session_count=session_count,
        latest_category=latest_category,
        trend=trend,
    )

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=wellbeing_report_{user_id}.pdf"},
    )