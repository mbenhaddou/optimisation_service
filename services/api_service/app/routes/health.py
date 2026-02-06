from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from ..config import settings
from ..db import engine

try:  # optional import for readiness check
    import redis
except ModuleNotFoundError:  # pragma: no cover
    redis = None

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/ready")
def ready():
    db_ok = True
    redis_ok = True

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    if settings.redis_url and redis is not None:
        try:
            redis.Redis.from_url(settings.redis_url).ping()
        except Exception:
            redis_ok = False

    overall_ok = db_ok and redis_ok
    payload = {"status": "ok" if overall_ok else "degraded", "db_ok": db_ok, "redis_ok": redis_ok}
    return JSONResponse(status_code=200 if overall_ok else 503, content=payload)
