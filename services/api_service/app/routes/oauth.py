from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import User
from ..schemas import TokenResponse, UserProfileResponse
from ..services.auth import create_access_token, verify_password
from pydantic import BaseModel

router = APIRouter(prefix="/v1/oauth", tags=["oauth"])


def get_db() -> Session:
    yield from get_session()


class OAuthTokenRequest(BaseModel):
    username: str
    password: str


@router.post("/token", response_model=TokenResponse)
def token(
    payload: OAuthTokenRequest,
    request: Request = None,
    db: Session = Depends(get_db),
):
    email = payload.username.strip().lower()
    user = db.query(User).filter(User.email == email, User.is_active.is_(True)).one_or_none()
    try:
        valid = user is not None and verify_password(payload.password, user.hashed_password)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token_value = create_access_token(user.id, user.org_id, user.role)
    return TokenResponse(access_token=token_value)


@router.get("/userinfo", response_model=UserProfileResponse)
def userinfo(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = auth_header.split(" ", 1)[1].strip()
    from ..services.auth import decode_token

    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
