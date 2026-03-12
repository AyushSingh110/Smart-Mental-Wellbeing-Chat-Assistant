
from __future__ import annotations
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.config import settings
from backend.database.mongo_client import MongoClient
from backend.database.schemas import HealthCheckResponse, UserTrendResponse
from backend.dependencies import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin"])

# GET liveness probe
@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Application health check",
)
async def health_check() -> HealthCheckResponse:
    return HealthCheckResponse(
        status="ok",
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow(),
    )

# GET longitudinal MHI trend
@router.get(
    "/user/{user_id}/trend",
    response_model=UserTrendResponse,
    summary="Get MHI trend for a user over the last N days",
)
async def user_trend(
    user_id: str,
    days: int = Query(default=30, ge=1, le=365),
    db: MongoClient = Depends(get_db),
) -> UserTrendResponse:
    user = await db.get_or_create_user(user_id)
    history = await db.get_mhi_history(user_id, days=days)

    if not history:
        return UserTrendResponse(
            user_id=user_id,
            mhi_history=[],
            average_mhi=user.get("latest_mhi", 100.0),
            trend_direction="stable",
        )

    mhi_points = [
        {
            "mhi": h["matrix"]["mhi"],
            "timestamp": h["timestamp"].isoformat() if isinstance(h["timestamp"], datetime) else str(h["timestamp"]),
        }
        for h in history
    ]
    values = [p["mhi"] for p in mhi_points]
    avg = round(sum(values) / len(values), 2)

    # Simple trend direction
    if len(values) >= 3:
        first_half = sum(values[: len(values) // 2]) / (len(values) // 2)
        second_half = sum(values[len(values) // 2 :]) / (len(values) - len(values) // 2)
        diff = second_half - first_half
        if diff > 3:
            direction = "improving"
        elif diff < -3:
            direction = "declining"
        else:
            direction = "stable"
    else:
        direction = "stable"

    return UserTrendResponse(
        user_id=user_id,
        mhi_history=mhi_points,
        average_mhi=avg,
        trend_direction=direction,
    )



# GET alias used by Streamlit
@router.get(
    "/user/{user_id}/timeline",
    summary="MHI timeline (flat list for Streamlit chart)",
)
async def user_timeline(
    user_id: str,
    days: int = Query(default=30, ge=1, le=365),
    db: MongoClient = Depends(get_db),
):
    """
    Returns a flat list of {mhi, category, timestamp} dicts
    that Streamlit can feed directly into a Plotly line chart.
    """
    history = await db.get_mhi_history(user_id, days=days)
    return [
        {
            "mhi": h["matrix"]["mhi"],
            "timestamp": h["timestamp"].isoformat()
            if isinstance(h["timestamp"], datetime)
            else str(h["timestamp"]),
        }
        for h in history
    ]

# GETrecent conversations
@router.get(
    "/user/{user_id}/history",
    summary="Get recent conversation history for a user",
)
async def user_history(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    db: MongoClient = Depends(get_db),
):
    conversations = await db.get_recent_conversations(user_id, limit=limit)
    # Strip MongoDB _id (ObjectId is not JSON‑serializable)
    for c in conversations:
        c.pop("_id", None)
    return {"user_id": user_id, "count": len(conversations), "conversations": conversations}