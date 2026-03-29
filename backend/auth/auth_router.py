from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from bson import ObjectId

from backend.models.user_models import (
    UserRegister,
    UserLogin,
    TokenResponse,
    GoogleTokenRequest,
    UserResponse,
)
from backend.auth.auth_utils import hash_password, verify_password, create_access_token
from backend.database.mongo_client import db
from backend.config import settings
from backend.dependencies import get_current_user

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


@router.post("/google", response_model=TokenResponse)
async def google_login(payload: GoogleTokenRequest):
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Google login is not configured")

    try:
        id_info = id_token.verify_oauth2_token(
            payload.credential,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid Google credential") from exc

    email = (id_info.get("email") or "").strip().lower()
    if not email or not id_info.get("email_verified", False):
        raise HTTPException(status_code=401, detail="Google account email is not verified")

    now = datetime.utcnow()
    google_sub = id_info.get("sub")
    name = id_info.get("name") or email.split("@")[0]
    picture = id_info.get("picture")

    user = await db.users.find_one({"email": email})
    if user:
        await db.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "google_sub": google_sub,
                    "name": name,
                    "picture": picture,
                    "auth_provider": "google",
                    "last_login": now,
                }
            },
        )
        user_id = str(user["_id"])
    else:
        result = await db.users.insert_one(
            {
                "email": email,
                "name": name,
                "picture": picture,
                "google_sub": google_sub,
                "auth_provider": "google",
                "hashed_password": hash_password(f"google-auth::{google_sub}::{email}"),
                "baseline_mhi": 75,
                "phq2_total": 0,
                "gad2_total": 0,
                "latest_mhi": 75,
                "created_at": now,
                "last_login": now,
            }
        )
        user_id = str(result.inserted_id)

    token = create_access_token(user_id)
    logger.info("User logged in with Google: %s", email)
    return {"access_token": token}


@router.get("/me", response_model=UserResponse)
async def me(user_id: ObjectId = Depends(get_current_user)):
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=str(user["_id"]),
        email=user.get("email", ""),
        name=user.get("name"),
        picture=user.get("picture"),
        baseline_mhi=int(user.get("baseline_mhi", 75)),
        created_at=user.get("created_at") or datetime.utcnow(),
        last_login=user.get("last_login"),
        auth_provider=user.get("auth_provider", "local"),
        phq2_total=int(user.get("phq2_total", 0)),
        gad2_total=int(user.get("gad2_total", 0)),
        latest_mhi=int(user.get("latest_mhi", user.get("baseline_mhi", 75))),
    )
