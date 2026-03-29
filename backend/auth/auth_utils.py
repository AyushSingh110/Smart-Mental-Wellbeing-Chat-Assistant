import base64
import hashlib
import hmac
from datetime import datetime, timedelta

from fastapi import HTTPException, status

from backend.config import settings

try:
    from jose import jwt as jose_jwt
    from jose import JWTError
except ImportError:  # pragma: no cover - depends on local env
    jose_jwt = None
    JWTError = Exception

try:
    import jwt as pyjwt
except ImportError:  # pragma: no cover - depends on local env
    pyjwt = None

try:
    from passlib.context import CryptContext
except ImportError:  # pragma: no cover - depends on local env
    CryptContext = None

SECRET_KEY = settings.JWT_SECRET
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET is not configured.")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") if CryptContext else None


def _hash_password_fallback(password: str) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), SECRET_KEY.encode("utf-8"), 120_000)
    return "pbkdf2_sha256$" + base64.b64encode(digest).decode("utf-8")


def hash_password(password: str) -> str:
    if pwd_context is not None:
        return pwd_context.hash(password)
    return _hash_password_fallback(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if pwd_context is not None:
        return pwd_context.verify(plain_password, hashed_password)
    return hmac.compare_digest(_hash_password_fallback(plain_password), hashed_password)


def _jwt_encode(payload: dict) -> str:
    if jose_jwt is not None:
        return jose_jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    if pyjwt is not None:
        return pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    raise RuntimeError("No JWT library available. Install python-jose or PyJWT.")


def _jwt_decode(token: str) -> dict:
    if jose_jwt is not None:
        return jose_jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if pyjwt is not None:
        return pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    raise RuntimeError("No JWT library available. Install python-jose or PyJWT.")


def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "exp": expire
    }
    return _jwt_encode(payload)


def decode_token(token: str):
    try:
        payload = _jwt_decode(token)
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
