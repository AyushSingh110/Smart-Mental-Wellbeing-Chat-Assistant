from backend.config import settings
from backend.database.mongo_client import MongoClient


def get_settings():
    return settings


def get_db() -> MongoClient:
    return MongoClient()