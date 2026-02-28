"""
FastAPI application entry-point.

Run with:
    uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

Then open in browser:
    http://127.0.0.1:8000        → API info (root)
    http://127.0.0.1:8000/docs   → Swagger UI (test all endpoints here)
    http://127.0.0.1:8000/health → Health check
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import routes_admin, routes_assessment, routes_chat
from backend.config import settings
from backend.database.mongo_client import mongo_client
from backend.services import (
    crisis_service,
    emotion_service,
    intent_service,
    llm_service,
    rag_service,
)

# ── Logging ──────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup + shutdown) ────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise heavyweight resources once, shut them down cleanly."""
    logger.info("Starting %s v%s …", settings.APP_NAME, settings.APP_VERSION)

    # 1. Database
    await mongo_client.connect()

    # 2. ML models (order doesn't matter – they're independent)
    await emotion_service.load_model()
    await crisis_service.load_model()
    await intent_service.load_model()

    # 3. RAG index
    await rag_service.load_index()

    # 4. LLM client
    await llm_service.init_client()

    logger.info("All services initialised – ready to serve requests.")

    yield  # ← application runs here

    # Shutdown
    await mongo_client.close()
    logger.info("Shutdown complete.")


# ── App factory ──────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "A production‑grade mental health monitoring engine with a chat "
        "interface. Detects emotion, crisis risk, computes a Mental Health "
        "Index (0‑100), and returns CBT‑grounded LLM responses."
    ),
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────
app.include_router(routes_chat.router)
app.include_router(routes_assessment.router)
app.include_router(routes_admin.router)


# ── Root route ───────────────────────────────────────
@app.get("/", summary="Root – API info")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "POST /chat": "Send a message through the analysis pipeline",
            "POST /assessment": "Submit PHQ-2 / GAD-2 screening",
            "GET /health": "Health check",
            "GET /user/{user_id}/trend": "MHI trend over time",
            "GET /user/{user_id}/history": "Conversation history",
        },
    }
