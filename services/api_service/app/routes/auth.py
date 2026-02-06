from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import Organization, User
from ..schemas import LoginRequest, RegisterRequest, TokenResponse
from ..services.auth import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/v1/auth", tags=["auth"])


def get_db() -> Session:
    yield from get_session()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _unique_org_name(db: Session, base_name: str) -> str:
    candidate = base_name
    suffix = 1
    while db.query(Organization).filter(Organization.name == candidate).first():
        suffix += 1
        candidate = f"{base_name}-{suffix}"
    return candidate


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = _normalize_email(payload.email)
    existing = db.query(User).filter(User.email == email).one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    org_name = payload.organization or email.split("@")[0].replace(".", " ").title()
    org_name = _unique_org_name(db, org_name)

    org = Organization(name=org_name)
    db.add(org)
    db.flush()

    try:
        hashed_password = hash_password(payload.password)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    user = User(
        email=email,
        hashed_password=hashed_password,
        role="owner",
        org_id=org.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    try:
        token = create_access_token(user.id, user.org_id, user.role)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = _normalize_email(payload.email)
    user = db.query(User).filter(User.email == email, User.is_active.is_(True)).one_or_none()
    try:
        valid = user is not None and verify_password(payload.password, user.hashed_password)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        token = create_access_token(user.id, user.org_id, user.role)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return TokenResponse(access_token=token)
