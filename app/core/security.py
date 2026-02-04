import hashlib
import hmac
import secrets
from typing import Optional

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