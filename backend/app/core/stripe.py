"""Stripe integration service."""

import asyncio
import stripe
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.core.config import settings
from app.models.tenant import SubscriptionStatus


# Initialize Stripe
stripe.api_key = settings.stripe_secret_key


# =============================================================================
# Async wrappers for Stripe SDK (which is synchronous)
# Using asyncio.to_thread to prevent blocking the event loop
# =============================================================================


def map_stripe_status(stripe_status: str) -> SubscriptionStatus:
    """Map Stripe subscription status to our SubscriptionStatus enum."""
    status_map = {
        "trialing": SubscriptionStatus.trialing,
        "active": SubscriptionStatus.active,
        "past_due": SubscriptionStatus.past_due,
        "canceled": SubscriptionStatus.canceled,
        "unpaid": SubscriptionStatus.unpaid,
        "incomplete": SubscriptionStatus.trialing,  # Treat as trialing
        "incomplete_expired": SubscriptionStatus.canceled,
        "paused": SubscriptionStatus.past_due,  # Treat paused as past_due
    }
    return status_map.get(stripe_status, SubscriptionStatus.canceled)


async def create_checkout_session(
    *,
    price_id: str,
    tenant_name: str,
    email: str,
    plan_id: int,
    display_name: Optional[str] = None,
    trial_days: int = 30,
    success_url: str,
    cancel_url: str,
) -> stripe.checkout.Session:
    """
    Create a Stripe Checkout session for new tenant signup.
    
    The tenant_name and other details are stored in metadata
    and retrieved when the webhook fires.
    """
    def _create():
        return stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            subscription_data={
                "trial_period_days": trial_days,
                "metadata": {
                    "tenant_name": tenant_name,
                    "plan_id": str(plan_id),
                },
            },
            customer_email=email,
            metadata={
                "tenant_name": tenant_name,
                "email": email,
                "plan_id": str(plan_id),
                "display_name": display_name or tenant_name.replace("-", " ").title(),
            },
            success_url=success_url,
            cancel_url=cancel_url,
            allow_promotion_codes=True,
        )
    
    return await asyncio.to_thread(_create)


async def create_billing_portal_session(
    customer_id: str,
    return_url: str,
) -> stripe.billing_portal.Session:
    """
    Create a Stripe Billing Portal session for subscription management.
    
    The portal allows customers to:
    - Update payment method
    - View invoices
    - Cancel subscription
    - Change plan (if configured in Stripe)
    """
    def _create():
        return stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
    
    return await asyncio.to_thread(_create)


async def get_subscription(subscription_id: str) -> Optional[stripe.Subscription]:
    """Get subscription details from Stripe."""
    def _get():
        try:
            return stripe.Subscription.retrieve(subscription_id)
        except stripe.error.StripeError:
            return None

    return await asyncio.to_thread(_get)


def get_subscription_period_end(subscription: stripe.Subscription) -> Optional[int]:
    """
    Extract current_period_end from a Stripe subscription.

    In newer Stripe API versions, period info is nested under items.data[0].
    This helper handles both old and new formats.
    """
    # Try direct attribute first (older API versions)
    period_end = subscription.get('current_period_end')
    if period_end:
        return period_end

    # Try items.data[0] (newer API versions with flexible billing)
    items = subscription.get('items')
    if items and items.get('data'):
        first_item = items['data'][0] if items['data'] else None
        if first_item:
            return first_item.get('current_period_end')

    return None


async def get_customer(customer_id: str) -> Optional[stripe.Customer]:
    """Get customer details from Stripe."""
    def _get():
        try:
            return stripe.Customer.retrieve(customer_id)
        except stripe.error.StripeError:
            return None
    
    return await asyncio.to_thread(_get)


async def cancel_subscription(
    subscription_id: str,
    at_period_end: bool = True,
) -> Optional[stripe.Subscription]:
    """
    Cancel a subscription.

    By default, cancels at period end to allow access until paid period expires.
    """
    def _cancel():
        try:
            if at_period_end:
                return stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True,
                )
            else:
                return stripe.Subscription.delete(subscription_id)
        except stripe.error.StripeError:
            return None

    return await asyncio.to_thread(_cancel)


async def resume_subscription(
    subscription_id: str,
) -> Optional[stripe.Subscription]:
    """
    Resume a subscription that was set to cancel at period end.

    This unsets cancel_at_period_end, allowing the subscription to continue.
    """
    def _resume():
        try:
            return stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False,
            )
        except stripe.error.StripeError:
            return None

    return await asyncio.to_thread(_resume)


async def update_subscription_plan(
    subscription_id: str,
    new_price_id: str,
    proration_behavior: str = "create_prorations",
) -> Optional[stripe.Subscription]:
    """
    Update subscription to a new plan.
    
    Proration behavior:
    - "create_prorations": Charge/credit for time used (default)
    - "none": No proration
    - "always_invoice": Create invoice immediately
    """
    def _update():
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Update the subscription item's price
            return stripe.Subscription.modify(
                subscription_id,
                items=[{
                    "id": subscription["items"]["data"][0]["id"],
                    "price": new_price_id,
                }],
                proration_behavior=proration_behavior,
            )
        except stripe.error.StripeError:
            return None
    
    return await asyncio.to_thread(_update)


def construct_webhook_event(
    payload: bytes,
    signature: str,
) -> stripe.Event:
    """
    Construct and verify a webhook event from Stripe.
    
    Raises stripe.error.SignatureVerificationError if invalid.
    """
    return stripe.Webhook.construct_event(
        payload,
        signature,
        settings.stripe_webhook_secret,
    )


def get_price_id_for_plan(plan_name: str, yearly: bool = False) -> Optional[str]:
    """Get the Stripe price ID for a plan name.

    Args:
        plan_name: The plan name (starter, professional, enterprise)
        yearly: If True, return yearly price ID; otherwise monthly

    Returns:
        Stripe price ID or None if not configured
    """
    if yearly:
        price_map = {
            "starter": settings.stripe_price_starter_yearly,
            "professional": settings.stripe_price_professional_yearly,
            "enterprise": None,  # Enterprise is custom-quoted
        }
    else:
        price_map = {
            "starter": settings.stripe_price_starter,
            "professional": settings.stripe_price_professional,
            "enterprise": settings.stripe_price_enterprise,
        }
    return price_map.get(plan_name.lower())


def is_stripe_configured() -> bool:
    """Check if Stripe is properly configured."""
    return bool(
        settings.stripe_secret_key
        and settings.stripe_webhook_secret
        and (
            settings.stripe_price_starter
            or settings.stripe_price_professional
            or settings.stripe_price_enterprise
        )
    )


# =============================================================================
# Super Admin Billing Management Functions
# =============================================================================


async def get_customer_invoices(
    customer_id: str,
    limit: int = 10,
) -> list:
    """
    Get recent invoices for a customer.

    Returns a list of invoice objects from Stripe.
    """
    def _get():
        try:
            return stripe.Invoice.list(
                customer=customer_id,
                limit=limit,
            ).data
        except stripe.error.StripeError:
            return []

    return await asyncio.to_thread(_get)


async def get_subscription_details(
    subscription_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Get detailed subscription info including billing period.

    Returns a dict with subscription details or None if not found.
    """
    def _get():
        try:
            sub = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": sub.id,
                "status": sub.status,
                "current_period_start": sub.current_period_start,
                "current_period_end": sub.current_period_end,
                "cancel_at_period_end": sub.cancel_at_period_end,
                "canceled_at": sub.canceled_at,
                "trial_start": sub.trial_start,
                "trial_end": sub.trial_end,
                "created": sub.created,
            }
        except stripe.error.StripeError:
            return None

    return await asyncio.to_thread(_get)


def get_stripe_dashboard_url(customer_id: str) -> str:
    """
    Get direct link to Stripe dashboard for a customer.

    Automatically detects test vs live mode based on API key.
    """
    # Detect test mode from API key
    is_test = "test" in (settings.stripe_secret_key or "").lower()
    mode = "test" if is_test else ""

    if mode:
        return f"https://dashboard.stripe.com/{mode}/customers/{customer_id}"
    return f"https://dashboard.stripe.com/customers/{customer_id}"
