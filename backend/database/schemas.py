from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


#  Chat

class ChatRequest(BaseModel):
    message: str
    language_code: str = "en"


class ChatResponse(BaseModel):
    response: str
    emotion_scores: dict
    crisis_score: float
    crisis_tier: str
    intent: str
    mhi: int
    category: str


#  Assessment 

class AssessmentRequest(BaseModel):
    phq2: int
    gad2: int


class SimpleAssessmentRequest(BaseModel):
    user_id: str
    phq2: int
    gad2: int


class AssessmentResponse(BaseModel):
    user_id: str
    phq2_score: int
    gad2_score: int
    screening_normalized: float
    timestamp: datetime


# Voice

class SpeakRequest(BaseModel):
    text: str
    emotion_label: str = "default"
    crisis_tier: str = "none"
    language_code: str = "en"


# Admin / Health 

class HealthCheckResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime


class UserTrendResponse(BaseModel):
    user_id: str
    mhi_history: list
    average_mhi: float
    trend_direction: str
