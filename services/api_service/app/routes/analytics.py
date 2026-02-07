from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..db import get_session
from ..schemas import AnalyticsRoutesResponse
from ..deps import get_current_user, require_roles
from ..services.analytics_service import build_routes_analytics

router = APIRouter(prefix="/v1/analytics", tags=["analytics"])


def get_db() -> Session:
    yield from get_session()


@router.get("/routes", response_model=AnalyticsRoutesResponse)
def analytics_routes(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    require_roles(user, {"owner", "admin", "manager", "analyst"})
    org_id = user.org_id
    return build_routes_analytics(db, org_id)
