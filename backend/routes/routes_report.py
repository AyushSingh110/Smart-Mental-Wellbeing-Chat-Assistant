from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from backend.database.mongo_client import MongoClient
from backend.dependencies import get_db
from backend.services.report_service import ReportService
from backend.services.llm_service import generate_llm_response

router = APIRouter(prefix="/report", tags=["Report"])
report_service = ReportService()


@router.get("/{user_id}")
async def generate_report(user_id: str, db: MongoClient = Depends(get_db)):

    conversations = await db.get_recent_conversations(user_id, limit=50)

    if not conversations:
        return {"error": "No session data available."}

    # Build conversation text
    conversation_text = "\n".join(
        [f"User: {c['message']}" for c in conversations]
    )

    summary_prompt = f"""
    Summarize this mental health session.
    Highlight:
    - Emotional patterns
    - Behavioral themes
    - Cognitive distortions
    - Overall mental health trend

    Conversation:
    {conversation_text}
    """

    summary = generate_llm_response(summary_prompt)

    mhi_values = [c["mhi"] for c in conversations if "mhi" in c]
    avg_mhi = round(sum(mhi_values) / len(mhi_values), 2)

    pdf_buffer = report_service.generate_pdf(
        user_id=user_id,
        summary=summary,
        mhi_avg=avg_mhi,
    )

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=session_report_{user_id}.pdf"
        },
    )