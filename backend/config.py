from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):

    # -- App -------------------------------------------------------------------
    APP_NAME: str = "Smart Mental Well-Being Chat Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # -- Database --------------------------------------------------------------
    MONGO_URI: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection string",
    )
    MONGO_DB_NAME: str = "smart_mental_health"

    # -- JWT Authentication ----------------------------------------------------
    JWT_SECRET: str = Field(
        default="change_this_to_a_secure_random_string",
        description="Secret key for JWT signing",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # -- API Keys --------------------------------------------------------------
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # -- Google OAuth -----------------------------------------------------------
    GOOGLE_CLIENT_ID: str = Field(default="")
    GOOGLE_CLIENT_SECRET: str = Field(default="")
    GOOGLE_REDIRECT_URI: str = Field(default="http://localhost:8000/auth/google/callback")
    FRONTEND_URL: str = Field(default="http://localhost:8501")

    # -- LLM Config ------------------------------------------------------------
    LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 1024

    # -- ML Models -------------------------------------------------------------
    EMOTION_MODEL_PATH: str = "models/emotion_distilbert"
    CRISIS_MODEL_PATH: str = "models/crisis_distilbert"
    SENTENCE_MODEL_NAME: str = "all-MiniLM-L6-v2"
    FAISS_INDEX_PATH: str = "models/faiss_cbt_index"

    # -- Thresholds ------------------------------------------------------------
    CRISIS_PROBABILITY_THRESHOLD: float = 0.65
    SAFETY_OVERRIDE_THRESHOLD: float = 0.80

    # -- MHI Weights -----------------------------------------------------------
    WEIGHT_EMOTION: float = 0.30
    WEIGHT_CRISIS: float = 0.25
    WEIGHT_SCREENING: float = 0.20
    WEIGHT_BEHAVIORAL: float = 0.10
    WEIGHT_HISTORY: float = 0.15

    # -- RAG -------------------------------------------------------------------
    RAG_TOP_K: int = 3
    RAG_CHUNK_SIZE: int = 512
    RAG_CHUNK_OVERLAP: int = 64

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()