#mongo_client.py
from __future__ import annotations

import logging
from typing import Any

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    _HAS_MOTOR = True
except ImportError:  # pragma: no cover - depends on local env
    from pymongo import MongoClient as SyncMongoClient

    AsyncIOMotorClient = None
    _HAS_MOTOR = False

from backend.config import settings

logger = logging.getLogger(__name__)


class _SyncCursorAdapter:
    def __init__(self, cursor):
        self._cursor = cursor

    def sort(self, *args, **kwargs):
        self._cursor = self._cursor.sort(*args, **kwargs)
        return self

    def limit(self, value: int):
        self._cursor = self._cursor.limit(value)
        return self

    async def to_list(self, length: int | None = None) -> list[dict]:
        docs = list(self._cursor)
        return docs if length is None else docs[:length]


class _SyncCollectionAdapter:
    def __init__(self, collection):
        self._collection = collection

    async def create_index(self, *args, **kwargs):
        return self._collection.create_index(*args, **kwargs)

    async def find_one(self, *args, **kwargs):
        return self._collection.find_one(*args, **kwargs)

    async def insert_one(self, *args, **kwargs):
        return self._collection.insert_one(*args, **kwargs)

    async def update_one(self, *args, **kwargs):
        return self._collection.update_one(*args, **kwargs)

    def find(self, *args, **kwargs):
        return _SyncCursorAdapter(self._collection.find(*args, **kwargs))


class Database:
    """
    Singleton MongoDB connection manager.

    Every module that needs the database imports the module-level ``db``
    instance instead of creating its own ``AsyncIOMotorClient``.
    """

    def __init__(self) -> None:
        # TLS is auto-enabled for mongodb+srv:// URIs;
        # for local mongodb:// URIs, TLS is off by default.
        if _HAS_MOTOR:
            self.client = AsyncIOMotorClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=15000,
                connectTimeoutMS=10000,
                maxPoolSize=10,
                connect=False,
            )
            db_handle = self.client[settings.MONGO_DB_NAME]
            self.db = db_handle
            self.users = db_handle["users"]
            self.conversations = db_handle["conversations"]
            self.assessments = db_handle["assessments"]
        else:
            self.client = SyncMongoClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=15000,
                connectTimeoutMS=10000,
                maxPoolSize=10,
                connect=False,
            )
            db_handle = self.client[settings.MONGO_DB_NAME]
            self.db = db_handle
            self.users = _SyncCollectionAdapter(db_handle["users"])
            self.conversations = _SyncCollectionAdapter(db_handle["conversations"])
            self.assessments = _SyncCollectionAdapter(db_handle["assessments"])
            logger.warning("motor not installed; using pymongo compatibility mode")

    # -- Lifecycle -------------------------------------------------------------

    async def create_indexes(self) -> None:
        """Create required indexes (idempotent — safe to call on every startup)."""
        try:
            await self.conversations.create_index([("user_id", 1), ("timestamp", -1)])
            await self.users.create_index("email", unique=True)
            logger.info("Database indexes ensured — database: %s", settings.MONGO_DB_NAME)
        except Exception as exc:
            logger.warning("Could not ensure indexes (DB may be temporarily unavailable): %s", exc)

    def close(self) -> None:
        self.client.close()
        logger.info("MongoDB connection closed.")

    # -- Convenience queries used by multiple routes ---------------------------

    async def get_recent_conversations(self, user_id, *, limit: int = 50) -> list[dict]:
        cursor = (
            self.conversations.find({"user_id": user_id})
            .sort("timestamp", -1)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def get_or_create_user(self, user_id: str) -> dict:
        user = await self.users.find_one({"_id": user_id})
        if not user:
            user = {"_id": user_id, "latest_mhi": 100.0}
            await self.users.insert_one(user)
        return user

    async def get_mhi_history(self, user_id: str, *, days: int = 30) -> list[dict]:
        from datetime import datetime, timedelta

        since = datetime.utcnow() - timedelta(days=days)
        cursor = (
            self.conversations.find(
                {"user_id": user_id, "timestamp": {"$gte": since}},
            )
            .sort("timestamp", 1)
        )
        return await cursor.to_list(length=1000)

    async def store_conversation(self, doc: dict) -> None:
        await self.conversations.insert_one(doc)

    async def store_assessment(self, doc: dict) -> None:
        await self.assessments.insert_one(doc)

    async def update_latest_mhi(self, user_id: str, mhi: float) -> None:
        await self.users.update_one(
            {"_id": user_id}, {"$set": {"latest_mhi": mhi}}, upsert=True,
        )

    async def update_assessment_scores(
        self, user_id: str, phq2: int, gad2: int, screening_norm: float,
    ) -> None:
        await self.users.update_one(
            {"_id": user_id},
            {"$set": {
                "phq2_total": phq2,
                "gad2_total": gad2,
                "screening_normalized": screening_norm,
            }},
            upsert=True,
        )


# -- Module-level singleton ----------------------------------------------------

db = Database()

# Backward-compat aliases (used by auth_router.py and legacy api/ routes)
MongoClient = Database
mongo_client = db
