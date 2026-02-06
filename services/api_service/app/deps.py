from typing import Optional

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from .config import settings
from .db import get_session
from .models import ApiKey, User
from .services.auth import decode_token


def get_db() -> Session:
    yield from get_session()


def get_api_key(request: Request, db: Session) -> Optional[str]:
    api_key = request.headers.get(settings.api_key_header)
    if not api_key:
        if settings.allow_anonymous:
            return None
        raise HTTPException(status_code=401, detail="Missing API key")

    key_row = db.query(ApiKey).filter(ApiKey.key == api_key, ApiKey.active.is_(True)).one_or_none()
    if key_row is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return key_row.id


def get_current_user(request: Request, db: Session) -> User:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = auth_header.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user
