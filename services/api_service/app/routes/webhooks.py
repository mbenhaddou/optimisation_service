from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import WebhookEndpoint
from ..schemas import WebhookCreate, WebhookListResponse, WebhookResponse
from ..deps import get_current_user, require_roles
from ..services import audit

router = APIRouter(prefix="/v1/webhooks", tags=["webhooks"])


def get_db() -> Session:
    yield from get_session()


@router.post("", response_model=WebhookResponse)
def create_webhook(payload: WebhookCreate, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    require_roles(user, {"owner", "admin", "manager"})
    webhook = WebhookEndpoint(
        name=payload.name,
        url=payload.url,
        events=payload.events,
        secret=payload.secret,
        active=bool(payload.active) if payload.active is not None else True,
        org_id=user.org_id,
    )
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    audit.record_event_safe(
        db,
        action="webhook.create",
        org_id=user.org_id,
        actor_user_id=user.id,
        target_type="webhook",
        target_id=webhook.id,
        metadata={"name": webhook.name, "events": webhook.events},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )
    return webhook


@router.get("", response_model=WebhookListResponse)
def list_webhooks(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    require_roles(user, {"owner", "admin", "manager"})
    items = (
        db.query(WebhookEndpoint)
        .filter(WebhookEndpoint.org_id == user.org_id)
        .order_by(WebhookEndpoint.created_at.desc())
        .all()
    )
    return WebhookListResponse(items=items, total=len(items))


@router.delete("/{webhook_id}")
def delete_webhook(webhook_id: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    require_roles(user, {"owner", "admin", "manager"})
    webhook = (
        db.query(WebhookEndpoint)
        .filter(WebhookEndpoint.id == webhook_id, WebhookEndpoint.org_id == user.org_id)
        .one_or_none()
    )
    if webhook is None:
        raise HTTPException(status_code=404, detail="Webhook not found")
    db.delete(webhook)
    db.commit()
    audit.record_event_safe(
        db,
        action="webhook.delete",
        org_id=user.org_id,
        actor_user_id=user.id,
        target_type="webhook",
        target_id=webhook_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )
    return {"status": "deleted"}
