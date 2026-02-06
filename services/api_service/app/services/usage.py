from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import UsageRecord


def compute_node_count(payload: Dict[str, Any]) -> int:
    orders = payload.get("orders") or payload.get("work_orders") or []
    try:
        order_count = len(orders)
    except TypeError:
        order_count = 0

    has_depot = bool(payload.get("depot"))
    if not has_depot and isinstance(payload.get("teams"), dict):
        for team in payload["teams"].values():
            if isinstance(team, dict) and team.get("depot"):
                has_depot = True
                break

    return order_count + (1 if has_depot else 0)


def compute_usage_units(payload: Dict[str, Any]) -> int:
    node_count = compute_node_count(payload)
    return int(node_count * node_count)


def _month_window(now: Optional[datetime] = None) -> Tuple[datetime, datetime]:
    current = now or datetime.utcnow()
    start = current.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


def monthly_usage_units(
    db: Session,
    api_key_id: Optional[str] = None,
    org_id: Optional[str] = None,
    now: Optional[datetime] = None,
) -> int:
    start, end = _month_window(now)
    stmt = (
        select(func.coalesce(func.sum(UsageRecord.usage_units), 0))
        .where(UsageRecord.created_at >= start)
        .where(UsageRecord.created_at < end)
    )
    if org_id:
        stmt = stmt.where(UsageRecord.org_id == org_id)
    elif api_key_id:
        stmt = stmt.where(UsageRecord.api_key_id == api_key_id)
    return int(db.execute(stmt).scalar_one())
