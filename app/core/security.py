"""
Security utilities.

Includes:
- API key generation and verification
- Password hashing and verification
- JWT creation and validation
"""
import hashlib
import hmac
import secrets
from typing import Optional, Any

# === API KEY ===
def generate_api_key(prefix: str = "src") -> str:
    # Ex: src_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    return f"{prefix}_{secrets.token_urlsafe(32)}"

def hash_api_key(api_key: str) -> str:
    # SHA-256 hex (64 chars)
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()

def verify_api_key(api_key: str, expected_hash: Optional[str]) -> bool:
    if not expected_hash:
        return False
    candidate = hash_api_key(api_key)
    return hmac.compare_digest(candidate, expected_hash)

# === USER AUTH ===
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.settings import settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def create_access_token(*, sub: str, role: str, user_id: int, expires_min: Optional[int] = None) -> str:
    minutes = expires_min if expires_min is not None else settings.JWT_EXPIRES_MIN
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=minutes)

    payload: dict[str, Any] = {
        "sub": sub,
        "role": role,
        "uid": user_id,
        "iat": int(now.timestamp()),
        "exp": exp,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except JWTError as e:
        raise ValueError("invalid_token") from e