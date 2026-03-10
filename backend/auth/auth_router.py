from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

from backend.models.user_models import UserRegister, UserLogin, TokenResponse
from backend.auth.auth_utils import hash_password, verify_password, create_access_token
from backend.database.mongo_client import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# -- REGISTER ------------------------------------------------------------------

@router.post("/register", response_model=TokenResponse)
async def register(user: UserRegister):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(user.password)

    result = await db.users.insert_one({
        "email": user.email,
        "hashed_password": hashed,
        "baseline_mhi": user.baseline_mhi,
        "created_at": datetime.utcnow(),
        "last_login": None,
    })

    token = create_access_token(str(result.inserted_id))
    logger.info("New user registered: %s", user.email)
    return {"access_token": token}


# -- LOGIN ---------------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin):
    db_user = await db.users.find_one({"email": user.email})

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    await db.users.update_one(
        {"_id": db_user["_id"]},
        {"$set": {"last_login": datetime.utcnow()}},
    )

    token = create_access_token(str(db_user["_id"]))
    logger.info("User logged in: %s", user.email)
    return {"access_token": token}