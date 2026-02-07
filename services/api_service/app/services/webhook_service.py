from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from sqlalchemy.orm import Session

from ..models import WebhookEndpoint


def _sign_payload(secret: str, payload: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest


def list_webhooks(db: Session, org_id: Optional[str]) -> List[WebhookEndpoint]:
    query = db.query(WebhookEndpoint).order_by(WebhookEndpoint.created_at.desc())
    if org_id:
        query = query.filter(WebhookEndpoint.org_id == org_id)
    return query.all()


def send_webhook_events(
    db: Session,
    org_id: Optional[str],
    event: str,
    payload: Dict[str, Any],
) -> None:
    endpoints = list_webhooks(db, org_id)
    if not endpoints:
        return

    data = {
        "event": event,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": payload,
    }
    raw_payload = json.dumps(data)

    for endpoint in endpoints:
        if not endpoint.active:
            continue
        if endpoint.events and event not in endpoint.events:
            continue
        headers = {"Content-Type": "application/json"}
        if endpoint.secret:
            headers["X-Webhook-Signature"] = _sign_payload(endpoint.secret, raw_payload)
        try:
            requests.post(endpoint.url, data=raw_payload, headers=headers, timeout=4)
        except Exception:
            continue
