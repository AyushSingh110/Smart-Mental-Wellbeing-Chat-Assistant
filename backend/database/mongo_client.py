"""
Async MongoDB client powered by Motor.

Exposes typed helpers for the collections used by the application and
handles connection lifecycle via startup / shutdown hooks.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from backend.config import settings

logger = logging.getLogger(__name__)


class MongoClient:
    """Thin wrapper around Motor that exposes domain‑specific helpers."""

    def __init__(self) -> None:
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None

    # ── lifecycle ─────────────────────────────────────

    async def connect(self) -> None:
        logger.info("Connecting to MongoDB at %s …", settings.MONGO_URI)
        self._client = AsyncIOMotorClient(
            settings.MONGO_URI,
            serverSelectionTimeoutMS=5000,
        )
        self._db = self._client[settings.MONGO_DB_NAME]
        try:
            # Verify the connection is alive
            await self._client.admin.command("ping")
            await self._ensure_indexes()
            logger.info("MongoDB connected – database: %s", settings.MONGO_DB_NAME)
        except Exception as exc:
            logger.warning(
                "⚠️  MongoDB not reachable (%s). The server will start but "
                "database operations will fail until MongoDB is available.",
                exc,
            )

    async def close(self) -> None:
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed.")

    async def _ensure_indexes(self) -> None:
        """Create indexes once on startup for fast queries."""
        await self.conversations.create_index([("user_id", 1), ("timestamp", -1)])
        await self.users.create_index("user_id", unique=True)
        await self.assessments.create_index([("user_id", 1), ("timestamp", -1)])

    # ── collection accessors ─────────────────────────

    @property
    def db(self) -> AsyncIOMotorDatabase:
        assert self._db is not None, "MongoClient.connect() not called yet"
        return self._db

    @property
    def conversations(self):
        return self.db["conversations"]

    @property
    def users(self):
        return self.db["users"]

    @property
    def assessments(self):
        return self.db["assessments"]

    # ── user helpers ─────────────────────────────────

    async def get_or_create_user(self, user_id: str) -> Dict[str, Any]:
        user = await self.users.find_one({"user_id": user_id})
        if user is None:
            user = {
                "user_id": user_id,
                "created_at": datetime.utcnow(),
                "last_active": datetime.utcnow(),
                "total_sessions": 0,
                "latest_mhi": 100.0,
                "latest_category": "normal",
                "phq2_score": None,
                "gad2_score": None,
                "screening_normalized": 0.0,
                "behavioral_score": 0.0,
                "historical_trend_score": 0.0,
            }
            await self.users.insert_one(user)
            logger.info("Created new user profile: %s", user_id)
        return user

    async def update_user_after_chat(
        self,
        user_id: str,
        mhi: float,
        category: str,
        behavioral_score: float,
        historical_trend_score: float,
    ) -> None:
        await self.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "last_active": datetime.utcnow(),
                    "latest_mhi": mhi,
                    "latest_category": category,
                    "behavioral_score": behavioral_score,
                    "historical_trend_score": historical_trend_score,
                },
                "$inc": {"total_sessions": 1},
            },
        )

    async def update_assessment_scores(
        self,
        user_id: str,
        phq2: Optional[int],
        gad2: Optional[int],
        screening_normalized: float,
    ) -> None:
        await self.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "phq2_score": phq2,
                    "gad2_score": gad2,
                    "screening_normalized": screening_normalized,
                }
            },
        )

    # ── conversation helpers ─────────────────────────

    async def store_conversation(self, doc: Dict[str, Any]) -> str:
        result = await self.conversations.insert_one(doc)
        return str(result.inserted_id)

    async def get_recent_conversations(
        self, user_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        cursor = (
            self.conversations.find({"user_id": user_id})
            .sort("timestamp", -1)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    # ── assessment helpers ───────────────────────────

    async def store_assessment(self, doc: Dict[str, Any]) -> str:
        result = await self.assessments.insert_one(doc)
        return str(result.inserted_id)

    # ── trend / history helpers ──────────────────────

    async def get_mhi_history(
        self, user_id: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        cursor = (
            self.conversations.find(
                {"user_id": user_id, "timestamp": {"$gte": cutoff}},
                {"matrix.mhi": 1, "timestamp": 1, "_id": 0},
            )
            .sort("timestamp", 1)
        )
        return await cursor.to_list(length=500)

    async def compute_historical_trend_score(self, user_id: str) -> float:
        """
        Return a 0‑1 score representing recent MHI trajectory.
        0 = consistently healthy · 1 = consistently deteriorating.
        """
        history = await self.get_mhi_history(user_id, days=14)
        if len(history) < 2:
            return 0.0
        mhi_values = [h["matrix"]["mhi"] for h in history]
        # Simple linear slope normalised into [0, 1]
        n = len(mhi_values)
        x_mean = (n - 1) / 2
        y_mean = sum(mhi_values) / n
        numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(mhi_values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator else 0.0
        # Negative slope → worsening → higher risk score
        risk = max(0.0, min(1.0, -slope / 5.0))
        return round(risk, 4)


# Module‑level singleton
mongo_client = MongoClient()
