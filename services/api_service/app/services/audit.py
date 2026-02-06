from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from ..models import AuditLog


def build_event(
    action: str,
    org_id: Optional[str] = None,
    actor_user_id: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    return AuditLog(
        action=action,
        org_id=org_id,
        actor_user_id=actor_user_id,
        target_type=target_type,
        target_id=target_id,
        details=metadata,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def record_event(db: Session, **kwargs) -> AuditLog:
    event = build_event(**kwargs)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def record_event_safe(db: Session, **kwargs) -> Optional[AuditLog]:
    try:
        return record_event(db, **kwargs)
    except Exception:
        db.rollback()
        return None
