from typing import Optional

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from .config import settings
from .db import get_session
from .models import ApiKey


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
