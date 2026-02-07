from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from ..models import ReportSchedule
from ..services.analytics_service import build_routes_analytics
from ..services.webhook_service import send_webhook_events


def _parse_field(field: str, min_value: int, max_value: int) -> set[int]:
    field = field.strip()
    if field == "*":
        return set(range(min_value, max_value + 1))
    values = set()
    for part in field.split(","):
        if part.isdigit():
            values.add(int(part))
    return values


def next_run_after(schedule: str, after: datetime) -> Optional[datetime]:
    parts = schedule.strip().split()
    if len(parts) != 5:
        return None
    minute_set = _parse_field(parts[0], 0, 59)
    hour_set = _parse_field(parts[1], 0, 23)
    dom_set = _parse_field(parts[2], 1, 31)
    month_set = _parse_field(parts[3], 1, 12)
    dow_set = _parse_field(parts[4], 0, 6)

    candidate = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    for _ in range(60 * 24 * 14):
        if (
            candidate.minute in minute_set
            and candidate.hour in hour_set
            and candidate.day in dom_set
            and candidate.month in month_set
            and candidate.weekday() in dow_set
        ):
            return candidate
        candidate += timedelta(minutes=1)
    return None


def is_due(schedule: str, last_run_at: Optional[datetime], now: datetime) -> bool:
    base = last_run_at or (now - timedelta(days=1))
    next_run = next_run_after(schedule, base)
    return bool(next_run and next_run <= now)


def run_due_reports(db: Session, now: Optional[datetime] = None) -> int:
    if now is None:
        now = datetime.utcnow()
    reports = db.query(ReportSchedule).filter(ReportSchedule.active.is_(True)).all()
    run_count = 0
    for report in reports:
        if not report.schedule:
            continue
        if not is_due(report.schedule, report.last_run_at, now):
            continue
        payload = build_routes_analytics(db, report.org_id)
        send_webhook_events(
            db,
            report.org_id,
            "report.generated",
            {"report_id": report.id, "format": report.format, "payload": payload.model_dump()},
        )
        report.last_run_at = now
        run_count += 1
    db.commit()
    return run_count
