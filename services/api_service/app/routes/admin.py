import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_session
from ..models import ApiKey
from ..schemas import ApiKeyCreate, ApiKeyListResponse, ApiKeyResponse

router = APIRouter(prefix="/v1/admin", tags=["admin"])


def _require_admin(request: Request) -> None:
    if not settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Admin key not configured")
    header_value = request.headers.get(settings.admin_key_header)
    if header_value != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")


def get_db() -> Session:
    yield from get_session()


@router.post("/api-keys", response_model=ApiKeyResponse)
def create_api_key(payload: ApiKeyCreate, request: Request, db: Session = Depends(get_db)):
    _require_admin(request)
    key_value = secrets.token_urlsafe(32)
    api_key = ApiKey(key=key_value, name=payload.name)
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key


@router.get("/api-keys", response_model=ApiKeyListResponse)
def list_api_keys(request: Request, db: Session = Depends(get_db)):
    _require_admin(request)
    rows = db.query(ApiKey).order_by(ApiKey.created_at.desc()).all()
    return ApiKeyListResponse(items=rows, total=len(rows))


@router.delete("/api-keys/{api_key_id}", response_model=ApiKeyResponse)
def deactivate_api_key(api_key_id: str, request: Request, db: Session = Depends(get_db)):
    _require_admin(request)
    row = db.query(ApiKey).filter(ApiKey.id == api_key_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="API key not found")
    row.active = False
    db.commit()
    db.refresh(row)
    return row
