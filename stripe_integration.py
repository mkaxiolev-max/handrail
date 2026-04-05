#!/usr/bin/env python3
"""
Stripe integration — NS∞ / Handrail commercial layer.
All functions degrade gracefully when keys are pending / test mode.
"""
import os
import json
import hashlib
import hmac
import logging
from datetime import datetime, timezone
from typing import Any

import stripe

log = logging.getLogger(__name__)

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")

# Price IDs — populated from Stripe dashboard after LLC verification
_PRICE_IDS = {
    "handrail_pro":        os.environ.get("STRIPE_PRICE_ID_HANDRAIL_PRO",    "PRICE_ID_HANDRAIL_PRO_PENDING"),
    "handrail_enterprise": os.environ.get("STRIPE_PRICE_ID_HANDRAIL_ENT",    "PRICE_ID_HANDRAIL_ENT_PENDING"),
    "root_pro":            os.environ.get("STRIPE_PRICE_ID_ROOT_PRO",         "PRICE_ID_ROOT_PRO_PENDING"),
    "root_auto":           os.environ.get("STRIPE_PRICE_ID_ROOT_AUTO",        "PRICE_ID_ROOT_AUTO_PENDING"),
}

_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")


def _is_pending(val: str) -> bool:
    return not val or "PENDING" in val or val.startswith("PRICE_ID")


def _key_ready() -> bool:
    key = stripe.api_key or ""
    return bool(key) and not _is_pending(key)


# ─── Legacy subscription helper (kept for backwards compat) ────────────────

def create_subscription(email: str, plan: str) -> dict:
    if plan == "free":
        return {"status": "active", "plan": "free", "customer_id": None}
    price_key = f"handrail_{plan}"
    price_id = _PRICE_IDS.get(price_key, "")
    if _is_pending(price_id) or not _key_ready():
        return {"status": "pending", "message": "Stripe keys not yet configured — Ring 5 activation required"}
    try:
        customer = stripe.Customer.create(email=email)
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{"price": price_id}],
        )
        return {
            "status": "active",
            "plan": plan,
            "customer_id": customer.id,
            "subscription_id": subscription.id,
        }
    except stripe.error.StripeError as exc:
        log.error("create_subscription error: %s", exc)
        return {"status": "error", "message": str(exc)}


def verify_subscription(customer_id: str) -> dict:
    if not _key_ready():
        return {"status": "pending", "message": "Stripe keys not configured"}
    try:
        subs = stripe.Subscription.list(customer=customer_id, limit=1)
        if subs.data:
            nickname = subs.data[0].items.data[0].price.nickname or "unknown"
            return {"status": "active", "plan": nickname}
        return {"status": "inactive"}
    except stripe.error.StripeError as exc:
        log.error("verify_subscription error: %s", exc)
        return {"status": "error", "message": str(exc)}


# ─── Checkout Session ───────────────────────────────────────────────────────

def create_checkout_session(
    email: str,
    plan: str,
    success_url: str = "https://axiolevruntime.vercel.app?checkout=success",
    cancel_url: str  = "https://axiolevruntime.vercel.app?checkout=cancel",
) -> dict:
    """
    Create a Stripe Checkout Session for a subscription plan.
    Returns {url} on success, {pending: True} when keys not configured.
    Supported plans: handrail_pro, handrail_enterprise, root_pro, root_auto.
    """
    price_id = _PRICE_IDS.get(plan, "")
    if _is_pending(price_id) or not _key_ready():
        return {
            "pending": True,
            "message": "Stripe keys not yet configured — complete Ring 5 activation.",
        }
    try:
        session = stripe.checkout.Session.create(
            customer_email=email,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"plan": plan, "product": "ns_infinity"},
        )
        return {"url": session.url, "session_id": session.id}
    except stripe.error.StripeError as exc:
        log.error("create_checkout_session error: %s", exc)
        return {"error": str(exc)}


# ─── Webhook Verification ───────────────────────────────────────────────────

def verify_webhook(payload: bytes, sig_header: str) -> dict[str, Any] | None:
    """
    Verify a Stripe webhook signature and return the parsed event dict,
    or None if verification fails.
    """
    if not _webhook_secret := (_WEBHOOK_SECRET or os.environ.get("STRIPE_WEBHOOK_SECRET", "")):
        log.warning("STRIPE_WEBHOOK_SECRET not set — webhook unverified")
        try:
            return json.loads(payload)
        except Exception:
            return None
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, _webhook_secret)
        return dict(event)
    except (stripe.error.SignatureVerificationError, ValueError) as exc:
        log.error("webhook verification failed: %s", exc)
        return None


# ─── Event Handlers ─────────────────────────────────────────────────────────

def handle_checkout_complete(event: dict[str, Any]) -> dict:
    """
    Process checkout.session.completed — provision access, emit receipt.
    Returns a TypedStateDelta-compatible dict.
    """
    session = event.get("data", {}).get("object", {})
    customer_id = session.get("customer")
    email = session.get("customer_email") or session.get("customer_details", {}).get("email")
    plan = session.get("metadata", {}).get("plan", "unknown")
    sub_id = session.get("subscription")
    ts = datetime.now(timezone.utc).isoformat()

    delta = {
        "type": "commercial.checkout_complete",
        "ts": ts,
        "customer_id": customer_id,
        "email": email,
        "plan": plan,
        "subscription_id": sub_id,
        "source": "stripe_webhook",
    }
    log.info("checkout_complete: plan=%s email=%s customer=%s", plan, email, customer_id)
    return delta


def handle_subscription_cancelled(event: dict[str, Any]) -> dict:
    """
    Process customer.subscription.deleted — revoke access, emit receipt.
    """
    sub = event.get("data", {}).get("object", {})
    customer_id = sub.get("customer")
    plan_items = sub.get("items", {}).get("data", [])
    plan_price = plan_items[0].get("price", {}).get("nickname", "unknown") if plan_items else "unknown"
    ts = datetime.now(timezone.utc).isoformat()

    delta = {
        "type": "commercial.subscription_cancelled",
        "ts": ts,
        "customer_id": customer_id,
        "plan": plan_price,
        "subscription_id": sub.get("id"),
        "source": "stripe_webhook",
    }
    log.info("subscription_cancelled: customer=%s plan=%s", customer_id, plan_price)
    return delta


# ─── Active Subscriptions Query ─────────────────────────────────────────────

def get_active_subscriptions(limit: int = 20) -> dict:
    """
    List currently active subscriptions. Returns {subscriptions, count, pending}.
    """
    if not _key_ready():
        return {"pending": True, "count": 0, "subscriptions": []}
    try:
        subs = stripe.Subscription.list(status="active", limit=limit, expand=["data.customer"])
        results = []
        for s in subs.data:
            customer_email = ""
            if hasattr(s.customer, "email"):
                customer_email = s.customer.email or ""
            plan_name = ""
            if s.items.data:
                plan_name = s.items.data[0].price.nickname or s.items.data[0].price.id
            results.append({
                "subscription_id": s.id,
                "customer_id": s.customer if isinstance(s.customer, str) else s.customer.id,
                "customer_email": customer_email,
                "plan": plan_name,
                "status": s.status,
                "created": datetime.fromtimestamp(s.created, tz=timezone.utc).isoformat(),
            })
        return {"subscriptions": results, "count": len(results), "pending": False}
    except stripe.error.StripeError as exc:
        log.error("get_active_subscriptions error: %s", exc)
        return {"error": str(exc), "count": 0, "subscriptions": []}
