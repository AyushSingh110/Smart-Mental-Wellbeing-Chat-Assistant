"""
Centralised application configuration loaded from environment variables.
Uses pydantic‑settings so every value can be overridden via .env or OS env.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────
    APP_NAME: str = "Smart Mental Well-Being Chat Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── MongoDB ───────────────────────────────────────
    MONGO_URI: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection string",
    )
    MONGO_DB_NAME: str = "mental_wellbeing"

    # ── OpenAI / LLM ─────────────────────────────────
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 1024

    # ── Model paths ───────────────────────────────────
    EMOTION_MODEL_PATH: str = "models/emotion_distilbert"
    CRISIS_MODEL_PATH: str = "models/crisis_distilbert"
    SENTENCE_MODEL_NAME: str = "all-MiniLM-L6-v2"
    FAISS_INDEX_PATH: str = "models/faiss_cbt_index"

    # ── Safety thresholds ─────────────────────────────
    CRISIS_PROBABILITY_THRESHOLD: float = 0.65
    SAFETY_OVERRIDE_THRESHOLD: float = 0.80

    # ── Matrix weights (must sum to 1.0) ──────────────
    WEIGHT_EMOTION: float = 0.30
    WEIGHT_CRISIS: float = 0.25
    WEIGHT_SCREENING: float = 0.20
    WEIGHT_BEHAVIORAL: float = 0.10
    WEIGHT_HISTORY: float = 0.15

    # ── RAG ───────────────────────────────────────────
    RAG_TOP_K: int = 3
    RAG_CHUNK_SIZE: int = 512
    RAG_CHUNK_OVERLAP: int = 64

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
