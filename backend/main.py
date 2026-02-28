from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import routes_admin, routes_assessment, routes_chat
from backend.config import settings
from backend.database.mongo_client import mongo_client


logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s …", settings.APP_NAME, settings.APP_VERSION)

    await mongo_client.connect()

    logger.info("Database connected. Services will load lazily.")

    yield

    await mongo_client.close()
    logger.info("Shutdown complete.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "A production-grade mental health monitoring engine with a chat "
        "interface. Detects emotion, crisis risk, computes a Mental Health "
        "Index (0-100), and returns CBT-grounded LLM responses."
    ),
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(routes_chat.router)
app.include_router(routes_assessment.router)
app.include_router(routes_admin.router)


@app.get("/", summary="Root – API info")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }