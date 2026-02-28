from fastapi import Depends
from backend.config import settings
from backend.database.mongo_client import mongo_client, MongoClient

def get_settings():
    """
    Dependency to inject application settings.
    """
    return settings

def get_db() -> MongoClient:
    """
    Dependency to inject MongoDB client.
    Ensures a single shared client across requests.
    """
    return mongo_client