from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId

from backend.config import settings
from backend.database.mongo_client import MongoClient
from backend.auth.auth_utils import decode_token


# -------- Existing Dependency -------- #

def get_settings():
    return settings


def get_db() -> MongoClient:
    return MongoClient()


# -------- JWT Security Dependency -------- #

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    payload = decode_token(token)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return ObjectId(user_id)