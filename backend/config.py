from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    APP_NAME: str = "Smart Mental Well-Being Chat Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # MongoDB
    MONGO_URI: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection string",
    )
    MONGO_DB_NAME: str = "mental_wellbeing"

    # LLM
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 600

    # Model Paths (Aligned with your project structure)
    EMOTION_MODEL_PATH: str = "backend/models/emotion_model"
    CRISIS_MODEL_PATH: str = "backend/models/crisis_model"
    SENTENCE_MODEL_NAME: str = "all-MiniLM-L6-v2"
    FAISS_INDEX_PATH: str = "backend/rag/faiss_index.index"
    FAISS_METADATA_PATH: str = "backend/rag/metadata.json"

    # Thresholds
    CRISIS_PROBABILITY_THRESHOLD: float = 0.75
    SAFETY_OVERRIDE_THRESHOLD: float = 0.80

    # Matrix Weights
    WEIGHT_EMOTION: float = 0.30
    WEIGHT_CRISIS: float = 0.35
    WEIGHT_SCREENING: float = 0.15
    WEIGHT_BEHAVIORAL: float = 0.10
    WEIGHT_HISTORY: float = 0.10

    # RAG
    RAG_TOP_K: int = 3
    RAG_CHUNK_SIZE: int = 400
    RAG_CHUNK_OVERLAP: int = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()