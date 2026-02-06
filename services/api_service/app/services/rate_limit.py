import time
from typing import Optional

try:
    import redis
except ModuleNotFoundError:  # pragma: no cover - optional dependency for local tests
    redis = None
from fastapi import HTTPException

from ..config import settings

_redis_client: Optional[object] = None


def _get_redis() -> Optional[object]:
    global _redis_client
    if redis is None:
        return None
    if _redis_client is not None:
        return _redis_client
    try:
        _redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    except Exception:
        _redis_client = None
    return _redis_client


def _bucket_key(identifier: str, window_seconds: int) -> str:
    bucket = int(time.time() // window_seconds)
    return f"rate:{identifier}:{bucket}"


def enforce_rate_limit(identifier: str) -> None:
    if not settings.enable_rate_limiting:
        return
    limit = settings.rate_limit_per_minute
    if limit <= 0:
        return

    redis_client = _get_redis()
    if redis_client is None:
        return

    window_seconds = max(settings.rate_limit_window_seconds, 1)
    key = _bucket_key(identifier, window_seconds)
    try:
        count = redis_client.incr(key)
        if count == 1:
            redis_client.expire(key, window_seconds * 2)
        if count > limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
    except redis.RedisError:
        return
