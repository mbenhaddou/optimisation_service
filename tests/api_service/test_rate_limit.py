import pytest

pytest.importorskip("redis")

from fastapi import HTTPException

from services.api_service.app.config import settings
from services.api_service.app.services import rate_limit


class DummyRedis:
    def __init__(self):
        self.count = 0

    def incr(self, key):
        self.count += 1
        return self.count

    def expire(self, key, ttl):
        return True


def test_rate_limit_blocks_after_threshold(monkeypatch):
    dummy = DummyRedis()
    monkeypatch.setattr(rate_limit, "_get_redis", lambda: dummy)

    original_enabled = settings.enable_rate_limiting
    original_limit = settings.rate_limit_per_minute
    original_window = settings.rate_limit_window_seconds
    try:
        object.__setattr__(settings, "enable_rate_limiting", True)
        object.__setattr__(settings, "rate_limit_per_minute", 2)
        object.__setattr__(settings, "rate_limit_window_seconds", 60)

        rate_limit.enforce_rate_limit("test")
        rate_limit.enforce_rate_limit("test")
        with pytest.raises(HTTPException):
            rate_limit.enforce_rate_limit("test")
    finally:
        object.__setattr__(settings, "enable_rate_limiting", original_enabled)
        object.__setattr__(settings, "rate_limit_per_minute", original_limit)
        object.__setattr__(settings, "rate_limit_window_seconds", original_window)
