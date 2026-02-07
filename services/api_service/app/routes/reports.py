from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import ReportSchedule
from ..schemas import (
    ReportScheduleCreate,
    ReportScheduleListResponse,
    ReportScheduleResponse,
)
from ..deps import get_current_user, require_roles
from ..services import audit
from ..services.report_service import run_due_reports

router = APIRouter(prefix="/v1/reports", tags=["reports"])


def get_db() -> Session:
    yield from get_session()


@router.post("", response_model=ReportScheduleResponse)
def create_report(
    payload: ReportScheduleCreate, request: Request, db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    require_roles(user, {"owner", "admin", "manager"})
    report = ReportSchedule(
        name=payload.name,
        schedule=payload.schedule,
        format=payload.format,
        active=payload.active,
        org_id=user.org_id,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    audit.record_event_safe(
        db,
        action="report.create",
        org_id=user.org_id,
        actor_user_id=user.id,
        target_type="report",
        target_id=report.id,
        metadata={"name": report.name, "schedule": report.schedule},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )
    return report


@router.get("", response_model=ReportScheduleListResponse)
def list_reports(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    require_roles(user, {"owner", "admin", "manager", "analyst"})
    items = (
        db.query(ReportSchedule)
        .filter(ReportSchedule.org_id == user.org_id)
        .order_by(ReportSchedule.created_at.desc())
        .all()
    )
    return ReportScheduleListResponse(items=items, total=len(items))


@router.delete("/{report_id}")
def delete_report(report_id: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    require_roles(user, {"owner", "admin", "manager"})
    report = (
        db.query(ReportSchedule)
        .filter(ReportSchedule.id == report_id, ReportSchedule.org_id == user.org_id)
        .one_or_none()
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    db.delete(report)
    db.commit()
    audit.record_event_safe(
        db,
        action="report.delete",
        org_id=user.org_id,
        actor_user_id=user.id,
        target_type="report",
        target_id=report_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )
    return {"status": "deleted"}


@router.post("/run")
def run_reports(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    require_roles(user, {"owner", "admin"})
    count = run_due_reports(db)
    return {"status": "ok", "reports_run": count}
