import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import ApiKey, AuditLog, Organization, User
from ..schemas import (
    ApiKeyCreate,
    ApiKeyListResponse,
    ApiKeyResponse,
    ApiKeyRotateRequest,
    AuditLogListResponse,
    OrganizationResponse,
    UserProfileResponse,
    UserListResponse,
    UserRoleUpdate,
)
from ..deps import get_current_user, require_roles
from ..services import audit

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
        scopes=payload.scopes,
        expires_at=payload.expires_at,
        org_id=user.org_id,
        created_by_user_id=user.id,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    audit.record_event_safe(
        db,
        action="api_key.create",
        org_id=user.org_id,
        actor_user_id=user.id,
        target_type="api_key",
        target_id=api_key.id,
        metadata={"name": payload.name, "scopes": payload.scopes},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )
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


@router.post("/api-keys/{api_key_id}/rotate", response_model=ApiKeyResponse)
def rotate_api_key(
    api_key_id: str,
    payload: ApiKeyRotateRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    _require_admin(user.role)
    existing = (
        db.query(ApiKey)
        .filter(ApiKey.id == api_key_id, ApiKey.org_id == user.org_id)
        .one_or_none()
    )
    if existing is None:
        raise HTTPException(status_code=404, detail="API key not found")

    existing.active = False
    existing.revoked_at = datetime.now(timezone.utc)

    key_value = secrets.token_urlsafe(32)
    api_key = ApiKey(
        key=key_value,
        name=payload.name or existing.name,
        scopes=payload.scopes if payload.scopes is not None else existing.scopes,
        expires_at=payload.expires_at or existing.expires_at,
        org_id=existing.org_id,
        created_by_user_id=user.id,
        rotated_from_id=existing.id,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    audit.record_event_safe(
        db,
        action="api_key.rotate",
        org_id=user.org_id,
        actor_user_id=user.id,
        target_type="api_key",
        target_id=existing.id,
        metadata={"new_key_id": api_key.id},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )
    return api_key


@router.get("/audit", response_model=AuditLogListResponse)
def list_audit_logs(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    _require_admin(user.role)
    query = (
        db.query(AuditLog)
        .filter(AuditLog.org_id == user.org_id)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = query.all()
    total = db.query(AuditLog).filter(AuditLog.org_id == user.org_id).count()
    return AuditLogListResponse(items=items, total=total)


@router.get("/users", response_model=UserListResponse)
def list_users(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    require_roles(user, {"owner", "admin", "manager"})
    rows = (
        db.query(User)
        .filter(User.org_id == user.org_id)
        .order_by(User.created_at.desc())
        .all()
    )
    return UserListResponse(items=rows, total=len(rows))


@router.patch("/users/{user_id}", response_model=UserProfileResponse)
def update_user_role(
    user_id: str,
    payload: UserRoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    require_roles(user, {"owner", "admin"})
    target = (
        db.query(User)
        .filter(User.id == user_id, User.org_id == user.org_id)
        .one_or_none()
    )
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    target.role = payload.role
    db.commit()
    db.refresh(target)
    audit.record_event_safe(
        db,
        action="user.role.update",
        org_id=user.org_id,
        actor_user_id=user.id,
        target_type="user",
        target_id=target.id,
        metadata={"role": payload.role},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )
    return target
