"""
FastAPI dependency injection helpers.

Provides request‑scoped access to the MongoDB client and a reusable
database session without importing singletons directly in route modules.
"""

from __future__ import annotations

from backend.database.mongo_client import MongoClient, mongo_client


async def get_db() -> MongoClient:
    """Yield the application‑wide MongoClient singleton."""
    return mongo_client
