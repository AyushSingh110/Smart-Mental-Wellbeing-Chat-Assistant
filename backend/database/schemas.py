# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


#  Chat

class ChatRequest(BaseModel):
    message: str
    language_code: str = "en"
    source: str = "text"


class ChatResponse(BaseModel):
    response: str
    emotion_scores: dict
    crisis_score: float
    crisis_tier: str
    intent: str
    mhi: int
    category: str
    cbt_technique_suggested: Optional[str] = None
    # ── Extended fields (Round 2)
    top_3_emotions: Optional[list] = None          # [(label, score), ...]
    emotion_complexity: Optional[float] = None     # std-dev of top-3 scores
    suppression_flagged: Optional[bool] = None     # masking/suppression detected
    crisis_velocity: Optional[float] = None        # rate of change in crisis score
    behavioral_profile: Optional[dict] = None      # per-category behavioral scores
    pre_voice_alert: Optional[bool] = None         # True if alert tone should play
    mhi_trajectory: Optional[str] = None           # "improving"|"declining"|"stable"|"volatile"


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


# Avatar

class AvatarSpeakRequest(BaseModel):
    text: str
    language_code: str = "en"
    avatar_id: str = "therapist"
    emotion_label: str = "default"
    crisis_tier: str = "none"


# User Profile Update

class UserProfileUpdate(BaseModel):
    avatar_id: Optional[str] = None
    preferred_language: Optional[str] = None


# CBT

class CBTSessionCreate(BaseModel):
    technique: str
    notes: str = ""
    completed: bool = False


# Mood Journal

class MoodJournalEntry(BaseModel):
    mood_rating: int        # 1-10
    notes: str = ""


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
