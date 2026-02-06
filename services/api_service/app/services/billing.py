from datetime import datetime
from typing import Optional

try:
    import stripe
except ModuleNotFoundError:  # pragma: no cover
    stripe = None

from sqlalchemy.orm import Session

from ..config import settings
from ..models import BillingAccount, Organization
from ..services.usage import monthly_usage_units


def _require_stripe():
    if stripe is None:
        raise RuntimeError("stripe library is not installed")
    if not settings.stripe_secret_key:
        raise RuntimeError("STRIPE_SECRET_KEY is not configured")
    stripe.api_key = settings.stripe_secret_key


def get_or_create_billing_account(db: Session, org_id: str) -> BillingAccount:
    account = db.query(BillingAccount).filter(BillingAccount.org_id == org_id).one_or_none()
    if account:
        return account
    account = BillingAccount(
        org_id=org_id,
        plan_name="free",
        status="trialing",
        free_tier_units=settings.free_tier_units,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def billing_summary(db: Session, org_id: str):
    account = get_or_create_billing_account(db, org_id)
    used_units = monthly_usage_units(db, org_id=org_id)
    free_units = account.free_tier_units or settings.free_tier_units
    overage = max(0, used_units - (free_units or 0))
    return {
        "plan_name": account.plan_name,
        "status": account.status,
        "used_units": used_units,
        "free_tier_units": free_units,
        "overage_units": overage,
    }


def create_checkout_session(db: Session, org: Organization, success_url: str, cancel_url: str) -> str:
    _require_stripe()
    if not settings.stripe_price_id:
        raise RuntimeError("STRIPE_PRICE_ID is not configured")

    account = get_or_create_billing_account(db, org.id)
    if not account.stripe_customer_id:
        customer = stripe.Customer.create(name=org.name)
        account.stripe_customer_id = customer.id
        db.commit()

    session = stripe.checkout.Session.create(
        customer=account.stripe_customer_id,
        mode="subscription",
        line_items=[{"price": settings.stripe_price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.url


def create_billing_portal_session(db: Session, org: Organization, return_url: str) -> str:
    _require_stripe()
    account = get_or_create_billing_account(db, org.id)
    if not account.stripe_customer_id:
        customer = stripe.Customer.create(name=org.name)
        account.stripe_customer_id = customer.id
        db.commit()

    session = stripe.billing_portal.Session.create(
        customer=account.stripe_customer_id,
        return_url=return_url,
    )
    return session.url
