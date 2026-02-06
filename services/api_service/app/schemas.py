from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class RegisterRequest(BaseModel):
    email: str
    password: str
    organization: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OrganizationResponse(BaseModel):
    id: str
    name: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    id: str
    email: str
    role: str
    org_id: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApiKeyCreate(BaseModel):
    name: Optional[str] = None
    scopes: Optional[List[str]] = None
    expires_at: Optional[datetime] = None


class ApiKeyRotateRequest(BaseModel):
    name: Optional[str] = None
    scopes: Optional[List[str]] = None
    expires_at: Optional[datetime] = None


class ApiKeyResponse(BaseModel):
    id: str
    key: str
    name: Optional[str] = None
    scopes: Optional[List[str]] = None
    active: bool
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    last_used_ip: Optional[str] = None
    rotated_from_id: Optional[str] = None
    revoked_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    org_id: Optional[str] = None
    created_by_user_id: Optional[str] = None

    class Config:
        from_attributes = True


class ApiKeyListResponse(BaseModel):
    items: List[ApiKeyResponse]
    total: int


class AuditLogResponse(BaseModel):
    id: str
    org_id: Optional[str] = None
    actor_user_id: Optional[str] = None
    action: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int


class BillingSummaryResponse(BaseModel):
    plan_name: str
    status: str
    used_units: int
    free_tier_units: int
    overage_units: int


class BillingCheckoutResponse(BaseModel):
    url: str


class BillingPortalResponse(BaseModel):
    url: str


class JobResponse(BaseModel):
    id: str
    status: str
    node_count: Optional[int] = None
    usage_units: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    items: List[JobResponse]
    total: int
