from fastapi import APIRouter, HTTPException
from datetime import datetime

from backend.models.user_models import UserRegister, UserLogin, TokenResponse
from backend.auth.auth_utils import hash_password, verify_password, create_access_token
from backend.database.mongo_client import mongo_client

router = APIRouter(prefix="/auth", tags=["Authentication"])


# =========================
# REGISTER
# =========================
@router.post("/register", response_model=TokenResponse)
async def register(user: UserRegister):

    existing_user = await mongo_client.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(user.password)

    new_user = {
        "email": user.email,
        "hashed_password": hashed_password,
        "baseline_mhi": user.baseline_mhi,
        "created_at": datetime.utcnow(),
        "last_login": None
    }

    result = await mongo_client.users.insert_one(new_user)

    token = create_access_token(str(result.inserted_id))

    return {"access_token": token}


# =========================
# LOGIN
# =========================
@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin):

    db_user = await mongo_client.users.find_one({"email": user.email})

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    await mongo_client.users.update_one(
        {"_id": db_user["_id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )

    token = create_access_token(str(db_user["_id"]))

    return {"access_token": token}