from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_session
from ..deps import get_current_user
from ..models import Organization
from ..schemas import BillingCheckoutResponse, BillingPortalResponse, BillingSummaryResponse
from ..services import billing as billing_service

router = APIRouter(prefix="/v1/billing", tags=["billing"])


def get_db() -> Session:
    yield from get_session()


def _get_org(db: Session, org_id: str) -> Organization:
    org = db.query(Organization).filter(Organization.id == org_id).one_or_none()
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.get("/summary", response_model=BillingSummaryResponse)
def billing_summary(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    summary = billing_service.billing_summary(db, user.org_id)
    return BillingSummaryResponse(**summary)


@router.post("/checkout", response_model=BillingCheckoutResponse)
def billing_checkout(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    org = _get_org(db, user.org_id)
    base_url = settings.frontend_base_url.rstrip("/")
    try:
        url = billing_service.create_checkout_session(
            db,
            org,
            success_url=f"{base_url}/portal?checkout=success",
            cancel_url=f"{base_url}/portal?checkout=cancel",
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return BillingCheckoutResponse(url=url)


@router.post("/portal", response_model=BillingPortalResponse)
def billing_portal(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    org = _get_org(db, user.org_id)
    base_url = settings.frontend_base_url.rstrip("/")
    try:
        url = billing_service.create_billing_portal_session(
            db, org, return_url=f"{base_url}/portal"
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return BillingPortalResponse(url=url)


@router.post("/webhook")
async def billing_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    try:
        event_type = billing_service.handle_webhook(db, payload, signature)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"received": True, "event_type": event_type}
