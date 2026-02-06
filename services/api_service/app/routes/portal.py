import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import ApiKey, Organization
from ..schemas import ApiKeyCreate, ApiKeyListResponse, ApiKeyResponse, OrganizationResponse, UserProfileResponse
from ..deps import get_current_user

router = APIRouter(prefix="/v1/portal", tags=["portal"])


def get_db() -> Session:
    yield from get_session()


def _require_admin(user_role: str) -> None:
    if user_role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Insufficient permissions")


@router.get("/me", response_model=UserProfileResponse)
def me(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return user


@router.get("/organization", response_model=OrganizationResponse)
def organization(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user.org_id:
        raise HTTPException(status_code=404, detail="Organization not found")
    org = db.query(Organization).filter(Organization.id == user.org_id).one_or_none()
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.post("/api-keys", response_model=ApiKeyResponse)
def create_api_key(payload: ApiKeyCreate, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    _require_admin(user.role)

    key_value = secrets.token_urlsafe(32)
    api_key = ApiKey(
        key=key_value,
        name=payload.name,
        org_id=user.org_id,
        created_by_user_id=user.id,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key


@router.get("/api-keys", response_model=ApiKeyListResponse)
def list_api_keys(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    rows = (
        db.query(ApiKey)
        .filter(ApiKey.org_id == user.org_id)
        .order_by(ApiKey.created_at.desc())
        .all()
    )
    return ApiKeyListResponse(items=rows, total=len(rows))
