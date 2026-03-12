from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId

from backend.config import settings
from backend.database.mongo_client import Database, db
from backend.auth.auth_utils import decode_token


# -- Settings dependency -------------------------------------------------------

def get_settings():
    return settings


# -- Database dependency (returns the module-level singleton) -------------------

def get_db() -> Database:
    return db


# -- JWT Security --------------------------------------------------------------

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> ObjectId:
    token = credentials.credentials
    payload = decode_token(token)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return ObjectId(user_id)