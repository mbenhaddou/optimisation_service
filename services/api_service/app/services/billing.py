from datetime import datetime, timezone
from typing import Any, Dict, Optional

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


def _to_datetime(value: Optional[int]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromtimestamp(int(value), tz=timezone.utc)


def _get_account_by_customer(db: Session, customer_id: str) -> Optional[BillingAccount]:
    if not customer_id:
        return None
    return (
        db.query(BillingAccount)
        .filter(BillingAccount.stripe_customer_id == customer_id)
        .one_or_none()
    )


def _extract_plan_name(subscription: Dict[str, Any]) -> Optional[str]:
    items = subscription.get("items", {}).get("data", []) if isinstance(subscription, dict) else []
    if not items:
        return None
    item = items[0] or {}
    price = item.get("price") or {}
    if price.get("nickname"):
        return price["nickname"]
    plan = item.get("plan") or {}
    if plan.get("nickname"):
        return plan["nickname"]
    if price.get("id"):
        return price["id"]
    if plan.get("id"):
        return plan["id"]
    return None


def _update_account_from_subscription(account: BillingAccount, subscription: Dict[str, Any]) -> None:
    account.stripe_subscription_id = subscription.get("id") or account.stripe_subscription_id
    account.status = subscription.get("status") or account.status
    plan_name = _extract_plan_name(subscription)
    if plan_name:
        account.plan_name = plan_name
    account.current_period_start = _to_datetime(subscription.get("current_period_start"))
    account.current_period_end = _to_datetime(subscription.get("current_period_end"))


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
        client_reference_id=org.id,
        metadata={"org_id": org.id},
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


def handle_webhook(db: Session, payload: bytes, signature: Optional[str]) -> str:
    _require_stripe()
    if not settings.stripe_webhook_secret:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET is not configured")
    if not signature:
        raise ValueError("Missing Stripe signature header")
    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.stripe_webhook_secret)
    except Exception as exc:  # pragma: no cover - stripe handles validation
        raise ValueError("Invalid Stripe webhook signature") from exc

    event_type = event.get("type", "")
    data_obj = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        customer_id = data_obj.get("customer")
        account = _get_account_by_customer(db, customer_id)
        if account:
            subscription_id = data_obj.get("subscription")
            if subscription_id:
                account.stripe_subscription_id = subscription_id
            if data_obj.get("status") == "complete":
                account.status = "active"
            db.commit()
    elif event_type in {
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    }:
        customer_id = data_obj.get("customer")
        account = _get_account_by_customer(db, customer_id)
        if account:
            _update_account_from_subscription(account, data_obj)
            db.commit()

    return event_type
