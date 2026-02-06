from datetime import datetime, timezone
from typing import Iterable, Optional, Set

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from .config import settings
from .db import get_session
from .models import ApiKey, User
from .services.auth import decode_token


def get_db() -> Session:
    yield from get_session()


def _normalize_scopes(scopes: Optional[Iterable[str] | str]) -> Set[str]:
    if scopes is None:
        return set()
    if isinstance(scopes, str):
        scopes = scopes.split(",")
    return {scope.strip() for scope in scopes if scope and str(scope).strip()}


def get_api_key(
    request: Request,
    db: Session,
    required_scopes: Optional[Iterable[str]] = None,
) -> Optional[str]:
    api_key = request.headers.get(settings.api_key_header)
    if not api_key:
        if settings.allow_anonymous:
            return None
        raise HTTPException(status_code=401, detail="Missing API key")

    key_row = db.query(ApiKey).filter(ApiKey.key == api_key, ApiKey.active.is_(True)).one_or_none()
    if key_row is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    if key_row.expires_at and key_row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="API key expired")

    if required_scopes:
        required = _normalize_scopes(required_scopes)
        existing = _normalize_scopes(key_row.scopes)
        if existing and not existing.issuperset(required):
            raise HTTPException(status_code=403, detail="API key missing required scope")

    key_row.last_used_at = datetime.now(timezone.utc)
    if request.client:
        key_row.last_used_ip = request.client.host
    db.commit()
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
