"""
Rate limiting configuration.

Defines the client key used for throttling requests (supports proxy/tests via X-Client-IP).
"""

import os
from slowapi import Limiter
from starlette.requests import Request


def client_key(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.headers.get("X-Real-IP") or (request.client.host if request.client else "127.0.0.1")

redis_url = os.getenv("REDIS_URL", "memory://")
# Usando o Redis como backend de storage para o SlowAPI
limiter = Limiter(key_func=client_key, storage_uri=redis_url) 