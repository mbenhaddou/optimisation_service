from datetime import datetime, timedelta
import os
from typing import Any, Dict, Optional

try:
    import jwt
except ModuleNotFoundError:  # pragma: no cover - optional in local tests
    jwt = None

try:
    from passlib.context import CryptContext
except ModuleNotFoundError:  # pragma: no cover - optional in local tests
    CryptContext = None

from ..config import settings


def _build_pwd_context() -> Optional["CryptContext"]:
    if CryptContext is None:
        return None
    scheme = os.getenv("PASSWORD_HASH_SCHEME", "bcrypt").strip() or "bcrypt"
    supported = ["bcrypt", "pbkdf2_sha256"]
    if scheme not in supported:
        scheme = "bcrypt"
    return CryptContext(schemes=supported, deprecated="auto", default=scheme)


pwd_context = _build_pwd_context()


def hash_password(password: str) -> str:
    if pwd_context is None:
        raise RuntimeError("passlib is required for password hashing")
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    if pwd_context is None:
        raise RuntimeError("passlib is required for password verification")
    return pwd_context.verify(password, hashed)


def create_access_token(subject: str, org_id: Optional[str], role: str) -> str:
    if jwt is None:
        raise RuntimeError("PyJWT is required for token creation")
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload: Dict[str, Any] = {
        "sub": subject,
        "org_id": org_id,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Dict[str, Any]:
    if jwt is None:
        raise RuntimeError("PyJWT is required for token decoding")
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
