"""
Assessment routes – PHQ‑2 / GAD‑2 self‑report screening.
"""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from backend.database.mongo_client import MongoClient
from backend.database.schemas import (
    AssessmentRequest,
    AssessmentResponse,
    SimpleAssessmentRequest,
)
from backend.dependencies import get_db
from backend.utils.scoring import normalise_screening

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assessment", tags=["Assessment"])


@router.post(
    "",
    response_model=AssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit PHQ‑2 / GAD‑2 screening (flat scores from Streamlit)",
)
async def submit_assessment(
    body: SimpleAssessmentRequest,
    db: MongoClient = Depends(get_db),
) -> AssessmentResponse:
    """
    Accepts flat PHQ‑2 and GAD‑2 total scores:
        { "user_id": "...", "phq2": 4, "gad2": 3 }
    Computes normalised screening score, persists, and updates user profile.
    """
    await db.get_or_create_user(body.user_id)

    phq2_score = body.phq2
    gad2_score = body.gad2
    screening_norm = normalise_screening(phq2_score, gad2_score)

    # Persist assessment doc
    assessment_doc = {
        "user_id": body.user_id,
        "phq2_score": phq2_score,
        "gad2_score": gad2_score,
        "screening_normalized": screening_norm,
        "timestamp": datetime.utcnow(),
    }
    await db.store_assessment(assessment_doc)

    # Update user profile
    await db.update_assessment_scores(body.user_id, phq2_score, gad2_score, screening_norm)

    logger.info(
        "[%s] Assessment stored – PHQ‑2=%s  GAD‑2=%s  norm=%.3f",
        body.user_id, phq2_score, gad2_score, screening_norm,
    )

    return AssessmentResponse(
        user_id=body.user_id,
        phq2_score=phq2_score,
        gad2_score=gad2_score,
        screening_normalized=screening_norm,
        timestamp=datetime.utcnow(),
    )
