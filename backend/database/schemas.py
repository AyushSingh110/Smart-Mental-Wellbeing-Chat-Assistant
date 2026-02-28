"""
Pydantic models used for request / response validation and MongoDB document shapes.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ────────────────────────────────────────────────────────
# Enums
# ────────────────────────────────────────────────────────

class MentalHealthCategory(str, Enum):
    NORMAL = "normal"
    MILD_STRESS = "mild_stress"
    ANXIETY = "anxiety"
    DEPRESSION_RISK = "depression_risk"
    CRISIS = "crisis"


class IntentType(str, Enum):
    VENTING = "venting"
    ADVICE_SEEKING = "advice_seeking"
    CRISIS = "crisis"
    CASUAL_TALK = "casual_talk"
    ASSESSMENT = "assessment"


# ────────────────────────────────────────────────────────
# Request schemas
# ────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """POST /chat body — only `message` is required."""
    message: str = Field(..., min_length=1, max_length=4096, description="User chat input (string)")
    user_id: str = Field(default="default_user", description="Optional user identifier (auto‑assigned if omitted)")


class AssessmentAnswer(BaseModel):
    question_id: str
    score: int = Field(..., ge=0, le=3)


class AssessmentRequest(BaseModel):
    """POST /assessment body – PHQ‑2 / GAD‑2 responses (structured)."""
    user_id: str
    answers: List[AssessmentAnswer]


class SimpleAssessmentRequest(BaseModel):
    """POST /assessment body – flat PHQ‑2 / GAD‑2 scores (from Streamlit)."""
    user_id: str
    phq2: int = Field(0, ge=0, le=6, description="PHQ‑2 total score (0‑6)")
    gad2: int = Field(0, ge=0, le=6, description="GAD‑2 total score (0‑6)")


# ────────────────────────────────────────────────────────
# Internal pipeline artifacts
# ────────────────────────────────────────────────────────

class EmotionResult(BaseModel):
    label: str = Field(..., description="Dominant emotion label")
    scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Full probability distribution over emotions",
    )
    confidence: float = Field(..., ge=0.0, le=1.0)


class IntentResult(BaseModel):
    intent: IntentType
    confidence: float = Field(..., ge=0.0, le=1.0)


class CrisisResult(BaseModel):
    is_crisis: bool = False
    probability: float = Field(0.0, ge=0.0, le=1.0)
    matched_keywords: List[str] = Field(default_factory=list)
    safety_override: bool = False


class MatrixResult(BaseModel):
    trs: float = Field(..., description="Total Risk Score (0‑1)")
    mhi: float = Field(..., description="Mental Health Index (0‑100)")
    category: MentalHealthCategory
    component_scores: Dict[str, float] = Field(default_factory=dict)


class RAGContext(BaseModel):
    documents: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)


# ────────────────────────────────────────────────────────
# Pipeline result (all stages combined)
# ────────────────────────────────────────────────────────

class PipelineResult(BaseModel):
    """Aggregated result of the full analysis pipeline."""
    preprocessed_text: str
    emotion: EmotionResult
    intent: IntentResult
    crisis: CrisisResult
    matrix: MatrixResult
    rag_context: RAGContext
    llm_response: str
    safety_flagged: bool = False
    processing_time_ms: float = 0.0


# ────────────────────────────────────────────────────────
# Response schemas
# ────────────────────────────────────────────────────────

class ChatResponse(BaseModel):
    """Returned to the client from POST /chat with all evaluation metrics."""
    user_id: str
    message: str = Field(..., description="Original user input")
    preprocessed_text: str = Field(..., description="Cleaned text fed to models")
    response: str = Field(..., description="Assistant reply")

    # ── Evaluation metrics ────────────────────────────
    emotion: EmotionResult = Field(..., description="Emotion classification result")
    intent: IntentResult = Field(..., description="Intent recognition result")
    crisis: CrisisResult = Field(..., description="Crisis detection result")
    mental_health: MatrixResult = Field(..., description="MHI score, TRS, category, component breakdown")

    # ── Meta ──────────────────────────────────────────
    safety_flagged: bool = Field(False, description="True if response was filtered by safety layer")
    processing_time_ms: float = Field(0.0, description="Pipeline latency in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AssessmentResponse(BaseModel):
    user_id: str
    phq2_score: Optional[int] = None
    gad2_score: Optional[int] = None
    screening_normalized: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheckResponse(BaseModel):
    status: str = "ok"
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UserTrendResponse(BaseModel):
    user_id: str
    mhi_history: List[Dict[str, float | str]]
    average_mhi: float
    trend_direction: str  # "improving" | "stable" | "declining"


# ────────────────────────────────────────────────────────
# MongoDB document shapes (stored as‑is)
# ────────────────────────────────────────────────────────

class ConversationDocument(BaseModel):
    """One turn of conversation persisted in MongoDB."""
    user_id: str
    message: str
    preprocessed_text: str
    response: str
    emotion: EmotionResult
    intent: IntentResult
    crisis: CrisisResult
    matrix: MatrixResult
    safety_flagged: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UserProfileDocument(BaseModel):
    """Persistent user profile."""
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    total_sessions: int = 0
    latest_mhi: float = 100.0
    latest_category: MentalHealthCategory = MentalHealthCategory.NORMAL
    phq2_score: Optional[int] = None
    gad2_score: Optional[int] = None
    screening_normalized: float = 0.0
    behavioral_score: float = 0.0
    historical_trend_score: float = 0.0
