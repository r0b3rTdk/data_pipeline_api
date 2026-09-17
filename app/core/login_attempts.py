"""
Redis-backed login attempt throttling.
Tracks failed attempts per IP and temporarily blocks after a threshold.
"""
import os
import redis
from datetime import timedelta

MAX_ATTEMPTS = 5
BLOCK_MINUTES = 10

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(redis_url, decode_responses=True)

def _key(ip: str) -> str:
    return f"bruteforce:{ip}"

def register_failure(ip: str) -> None:
    key = _key(ip)
    count = r.incr(key)
    # Define/renova o TTL (tempo de bloqueio) toda vez que atingir um marco critico
    if count == 1 or count >= MAX_ATTEMPTS:
        r.expire(key, timedelta(minutes=BLOCK_MINUTES))

def reset(ip: str) -> None:
    r.delete(_key(ip))

def is_blocked(ip: str) -> bool:
    count = r.get(_key(ip))
    return count is not None and int(count) >= MAX_ATTEMPTS

def reset_all() -> None:
    for key in r.scan_iter("bruteforce:*"):
        r.delete(key)