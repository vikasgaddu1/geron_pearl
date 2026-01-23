"""Billing and subscription management endpoints."""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash, get_current_user
from app.core.stripe import (
    create_checkout_session,
    create_billing_portal_session,
    construct_webhook_event,
    map_stripe_status,
    is_stripe_configured,
    get_subscription,
    get_subscription_period_end,
    cancel_subscription,
    resume_subscription,
)
from app.core.email import (
    send_welcome_email,
    send_payment_failed_email,
    send_subscription_canceled_email,
)
from app.crud import tenant as tenant_crud
from app.crud import user as user_crud
from app.db.session import get_db
from app.models.tenant import Tenant, SubscriptionStatus
from app.models.tenant_settings import TenantSettings, DEFAULT_TENANT_SETTINGS
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app.schemas.billing import (
    SignupInitiate,
    SignupInitiateResponse,
    BillingPortalResponse,
    BillingOverview,
    SubscriptionInfo,
    UsageInfo,
    PlanInfo,
    PlanListResponse,
    AutoRenewToggle,
    AutoRenewResponse,
)
from app.schemas.tenant import TenantCreate

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Helper Functions
# =============================================================================

async def _get_tenant_admin(db: AsyncSession, tenant_id: int) -> Optional[User]:
    """Get the admin user for a tenant (for sending billing emails)."""
    result = await db.execute(
        select(User).where(
            User.tenant_id == tenant_id,
            User.is_admin == True,
            User.is_active == True
        ).limit(1)
    )
    return result.scalar_one_or_none()


# =============================================================================
# Public Endpoints (No Auth Required)
# =============================================================================

@router.get("/plans", response_model=PlanListResponse)
async def list_plans(
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get list of available subscription plans.
    
    Public endpoint for pricing page.
    """
    result = await db.execute(
        select(SubscriptionPlan)
        .where(SubscriptionPlan.is_active == True)
        .order_by(SubscriptionPlan.sort_order)
    )
    plans = result.scalars().all()
    
    plan_list = []
    for plan in plans:
        plan_list.append(PlanInfo(
            id=plan.id,
            name=plan.name,
            display_name=plan.display_name,
            description=plan.description,
            price_monthly=plan.price_monthly,
            price_yearly=plan.price_yearly,
            max_users=plan.max_users,
            max_studies=plan.max_studies,
            max_tracker_items=getattr(plan, 'max_tracker_items', 1000),  # Fallback for pre-migration
            features=plan.features,
            is_popular=plan.is_popular,
        ))

    return PlanListResponse(plans=plan_list)


@router.post("/signup/initiate", response_model=SignupInitiateResponse)
async def initiate_signup(
    signup_data: SignupInitiate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Initiate tenant signup before Stripe checkout.
    
    Validates tenant name and email, then creates Stripe Checkout session.
    The actual tenant is created when webhook fires after successful payment.
    """
    if not is_stripe_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment processing is not configured",
        )
    
    # Validate tenant name is unique
    existing_tenant = await tenant_crud.get_by_name(db, name=signup_data.tenant_name)
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This organization name is already taken. Please choose another.",
        )
    
    # Validate email is not already used
    result = await db.execute(
        select(User).where(User.email == signup_data.email)
    )
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists. Please login instead.",
        )
    
    # Get the selected plan
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.id == signup_data.plan_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan selected",
        )
    
    # Determine which price ID to use based on billing period
    is_yearly = signup_data.billing_period == "yearly"
    price_id = plan.stripe_price_id_yearly if is_yearly else plan.stripe_price_id

    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This plan is not available for self-service signup. Please contact sales.",
        )

    # Create Stripe Checkout session
    display_name = signup_data.display_name or signup_data.tenant_name.replace("-", " ").title()

    session = await create_checkout_session(
        price_id=price_id,
        tenant_name=signup_data.tenant_name,
        email=signup_data.email,
        plan_id=plan.id,
        display_name=display_name,
        trial_days=settings.trial_period_days,
        success_url=f"{settings.frontend_url}/app/login?welcome=true&session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.frontend_url}/pricing?canceled=true",
    )
    
    return SignupInitiateResponse(
        checkout_url=session.url,
        session_id=session.id,
    )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Handle Stripe webhook events.
    
    Events handled:
    - checkout.session.completed: Create tenant and admin user
    - customer.subscription.updated: Update subscription status
    - customer.subscription.deleted: Mark subscription as canceled
    - invoice.payment_failed: Start grace period, send warning
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature",
        )
    
    try:
        event = construct_webhook_event(payload, sig_header)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook signature: {str(e)}",
        )
    
    event_type = event["type"]
    data = event["data"]["object"]
    
    # =========================================================================
    # checkout.session.completed - New signup
    # =========================================================================
    if event_type == "checkout.session.completed":
        customer_id = data.get("customer")
        subscription_id = data.get("subscription")
        metadata = data.get("metadata", {})
        
        # IDEMPOTENCY CHECK - Don't process twice
        existing_tenant = await tenant_crud.get_by_stripe_customer_id(
            db, stripe_customer_id=customer_id
        )
        if existing_tenant:
            return {"status": "already_processed"}
        
        # Extract signup data from metadata
        tenant_name = metadata.get("tenant_name")
        email = metadata.get("email")
        plan_id = int(metadata.get("plan_id", 1))
        display_name = metadata.get("display_name", tenant_name)
        
        if not tenant_name or not email:
            # Log error but return 200 to avoid Stripe retries
            return {"status": "error", "message": "Missing metadata"}
        
        # Create tenant
        tenant = await tenant_crud.create(
            db,
            obj_in=TenantCreate(
                name=tenant_name,
                display_name=display_name,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                subscription_status=SubscriptionStatus.trialing,
                trial_ends_at=datetime.utcnow() + timedelta(days=settings.trial_period_days),
                plan_id=plan_id,
            )
        )
        
        # Create TenantSettings with defaults
        tenant_settings = TenantSettings(
            tenant_id=tenant.id,
            **DEFAULT_TENANT_SETTINGS
        )
        db.add(tenant_settings)
        
        # Create admin user with random password (they'll set it via email)
        temp_password = secrets.token_urlsafe(16)
        admin_user = User(
            tenant_id=tenant.id,
            username=email.split("@")[0],
            email=email,
            password_hash=get_password_hash(temp_password),
            is_admin=True,
            is_active=True,
        )
        db.add(admin_user)
        await db.commit()
        
        # Send welcome email with login link
        login_url = f"{settings.frontend_url}/app/login?welcome=true"
        try:
            send_welcome_email(email, tenant.display_name, login_url)
            logger.info(f"Sent welcome email to {email} for tenant {tenant.name}")
        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}")

        return {"status": "success", "tenant_id": tenant.id}
    
    # =========================================================================
    # customer.subscription.updated - Status change
    # =========================================================================
    elif event_type == "customer.subscription.updated":
        subscription_id = data.get("id")
        stripe_status = data.get("status")
        
        tenant = await tenant_crud.get_by_stripe_subscription_id(
            db, stripe_subscription_id=subscription_id
        )
        if not tenant:
            return {"status": "tenant_not_found"}
        
        new_status = map_stripe_status(stripe_status)
        
        # Handle grace period for past_due
        if new_status == SubscriptionStatus.past_due:
            tenant.grace_period_ends_at = datetime.utcnow() + timedelta(
                days=settings.subscription_grace_period_days
            )
            # Send payment warning email to tenant admin
            admin_user = await _get_tenant_admin(db, tenant.id)
            if admin_user and admin_user.email:
                billing_url = f"{settings.frontend_url}/app/settings"
                try:
                    send_payment_failed_email(
                        admin_user.email,
                        tenant.display_name,
                        settings.subscription_grace_period_days,
                        billing_url
                    )
                    logger.info(f"Sent payment warning email to {admin_user.email}")
                except Exception as e:
                    logger.error(f"Failed to send payment warning email: {e}")
        
        tenant.subscription_status = new_status
        await db.commit()
        
        return {"status": "success", "new_status": new_status.value}
    
    # =========================================================================
    # customer.subscription.deleted - Cancellation
    # =========================================================================
    elif event_type == "customer.subscription.deleted":
        subscription_id = data.get("id")
        
        tenant = await tenant_crud.get_by_stripe_subscription_id(
            db, stripe_subscription_id=subscription_id
        )
        if not tenant:
            return {"status": "tenant_not_found"}
        
        tenant.subscription_status = SubscriptionStatus.canceled
        await db.commit()
        
        # Send cancellation confirmation email
        admin_user = await _get_tenant_admin(db, tenant.id)
        if admin_user and admin_user.email:
            reactivate_url = f"{settings.frontend_url}/pricing"
            try:
                send_subscription_canceled_email(
                    admin_user.email,
                    tenant.display_name,
                    reactivate_url
                )
                logger.info(f"Sent cancellation email to {admin_user.email}")
            except Exception as e:
                logger.error(f"Failed to send cancellation email: {e}")
        
        return {"status": "success"}
    
    # =========================================================================
    # invoice.payment_failed - Payment issue
    # =========================================================================
    elif event_type == "invoice.payment_failed":
        customer_id = data.get("customer")
        
        tenant = await tenant_crud.get_by_stripe_customer_id(
            db, stripe_customer_id=customer_id
        )
        if not tenant:
            return {"status": "tenant_not_found"}
        
        # Start grace period if not already in one
        if not tenant.grace_period_ends_at:
            tenant.grace_period_ends_at = datetime.utcnow() + timedelta(
                days=settings.subscription_grace_period_days
            )
            await db.commit()
            
            # Send payment failed email
            admin_user = await _get_tenant_admin(db, tenant.id)
            if admin_user and admin_user.email:
                billing_url = f"{settings.frontend_url}/app/settings"
                try:
                    send_payment_failed_email(
                        admin_user.email,
                        tenant.display_name,
                        settings.subscription_grace_period_days,
                        billing_url
                    )
                    logger.info(f"Sent payment failed email to {admin_user.email}")
                except Exception as e:
                    logger.error(f"Failed to send payment failed email: {e}")
        
        return {"status": "success"}
    
    # =========================================================================
    # invoice.paid - Payment successful (clears past_due state)
    # =========================================================================
    elif event_type == "invoice.paid":
        customer_id = data.get("customer")
        
        tenant = await tenant_crud.get_by_stripe_customer_id(
            db, stripe_customer_id=customer_id
        )
        if not tenant:
            return {"status": "tenant_not_found"}
        
        # Clear grace period and update status if we were in past_due
        if tenant.subscription_status == SubscriptionStatus.past_due:
            tenant.subscription_status = SubscriptionStatus.active
            tenant.grace_period_ends_at = None
            await db.commit()
            logger.info(f"Tenant {tenant.name} subscription reactivated after payment")
        
        return {"status": "success"}
    
    # Unhandled event type - acknowledge receipt
    return {"status": "ignored", "event_type": event_type}


# =============================================================================
# Authenticated Endpoints (Requires Login)
# =============================================================================

@router.get("/overview", response_model=BillingOverview)
async def get_billing_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get billing overview for current tenant.
    
    Returns subscription info and usage statistics.
    """
    tenant = await tenant_crud.get(db, id=current_user.tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    
    # Get plan info
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.id == tenant.plan_id)
    )
    plan = result.scalar_one_or_none()
    plan_name = plan.display_name if plan else "Unknown"
    plan_id = plan.id if plan else 0
    
    # Get usage counts
    from app.models.study import Study
    from app.models.reporting_effort_item_tracker import ReportingEffortItemTracker
    from app.models.reporting_effort_item import ReportingEffortItem
    from app.models.reporting_effort import ReportingEffort

    users_count = await db.scalar(
        select(func.count(User.id)).where(User.tenant_id == tenant.id)
    ) or 0

    studies_count = await db.scalar(
        select(func.count(Study.id)).where(Study.tenant_id == tenant.id)
    ) or 0

    # Tracker items don't have tenant_id directly - join through the hierarchy:
    # Tracker -> Item -> ReportingEffort -> Study (has tenant_id)
    tracker_items_count = await db.scalar(
        select(func.count(ReportingEffortItemTracker.id))
        .join(ReportingEffortItem, ReportingEffortItemTracker.reporting_effort_item_id == ReportingEffortItem.id)
        .join(ReportingEffort, ReportingEffortItem.reporting_effort_id == ReportingEffort.id)
        .join(Study, ReportingEffort.study_id == Study.id)
        .where(Study.tenant_id == tenant.id)
    ) or 0

    # Calculate limits (use getattr for max_tracker_items for backward compatibility)
    max_users = plan.max_users if plan else 5
    max_studies = plan.max_studies if plan else 10
    max_tracker_items = getattr(plan, 'max_tracker_items', 1000) if plan else 1000

    # Check if unlimited (-1)
    users_remaining = -1 if max_users == -1 else max(0, max_users - users_count)
    studies_remaining = -1 if max_studies == -1 else max(0, max_studies - studies_count)
    tracker_items_remaining = -1 if max_tracker_items == -1 else max(0, max_tracker_items - tracker_items_count)

    # Get subscription details from Stripe if available
    cancel_at_period_end = False
    current_period_end = None
    if tenant.stripe_subscription_id:
        stripe_sub = await get_subscription(tenant.stripe_subscription_id)
        if stripe_sub:
            # Use safe attribute access (Stripe SDK structure varies by version)
            cancel_at_period_end = stripe_sub.get('cancel_at_period_end', False)
            period_end = get_subscription_period_end(stripe_sub)
            if period_end:
                current_period_end = datetime.fromtimestamp(period_end)

    subscription_info = SubscriptionInfo(
        status=tenant.subscription_status,
        plan_name=plan_name,
        plan_id=plan_id,
        current_period_end=current_period_end,
        trial_ends_at=tenant.trial_ends_at,
        grace_period_ends_at=tenant.grace_period_ends_at,
        cancel_at_period_end=cancel_at_period_end,
    )
    
    usage_info = UsageInfo(
        users_count=users_count,
        users_limit=max_users,
        users_remaining=users_remaining,
        studies_count=studies_count,
        studies_limit=max_studies,
        studies_remaining=studies_remaining,
        tracker_items_count=tracker_items_count,
        tracker_items_limit=max_tracker_items,
        tracker_items_remaining=tracker_items_remaining,
    )
    
    # Check if tenant has Stripe billing configured
    has_billing_account = bool(tenant.stripe_customer_id and tenant.stripe_subscription_id)

    return BillingOverview(
        subscription=subscription_info,
        usage=usage_info,
        can_add_users=(max_users == -1 or users_count < max_users),
        can_add_studies=(max_studies == -1 or studies_count < max_studies),
        upgrade_available=(plan and plan.name != "enterprise"),
        has_billing_account=has_billing_account,
    )


@router.post("/portal", response_model=BillingPortalResponse)
async def create_portal_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create Stripe Billing Portal session.
    
    Redirects to Stripe's hosted portal for:
    - Updating payment method
    - Viewing invoices
    - Canceling subscription
    - Changing plan
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant admins can access billing",
        )
    
    tenant = await tenant_crud.get(db, id=current_user.tenant_id)
    if not tenant or not tenant.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No billing account found. Please contact support.",
        )
    
    session = await create_billing_portal_session(
        customer_id=tenant.stripe_customer_id,
        return_url=f"{settings.frontend_url}/app/billing",
    )
    
    return BillingPortalResponse(url=session.url)


@router.post("/auto-renew", response_model=AutoRenewResponse)
async def toggle_auto_renew(
    data: AutoRenewToggle,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Toggle auto-renewal for subscription.

    When cancel_auto_renew is True, the subscription will be canceled at the end
    of the current billing period. When False, auto-renewal is resumed.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant admins can manage billing",
        )

    tenant = await tenant_crud.get(db, id=current_user.tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    if not tenant.stripe_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription found. Please contact support.",
        )

    # Toggle auto-renewal via Stripe
    if data.cancel_auto_renew:
        result = await cancel_subscription(tenant.stripe_subscription_id, at_period_end=True)
        message = "Auto-renewal has been disabled. Your subscription will end at the current billing period."
    else:
        result = await resume_subscription(tenant.stripe_subscription_id)
        message = "Auto-renewal has been re-enabled. Your subscription will continue automatically."

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update subscription. Please try again or contact support.",
        )

    # Get current period end from result (using helper for Stripe API compatibility)
    period_end = get_subscription_period_end(result)
    current_period_end = datetime.fromtimestamp(period_end) if period_end else None

    return AutoRenewResponse(
        cancel_at_period_end=result.get('cancel_at_period_end', False),
        current_period_end=current_period_end,
        message=message,
    )


@router.get("/status")
async def check_stripe_status() -> Any:
    """
    Check if Stripe is configured (for frontend to show/hide billing features).
    """
    return {
        "stripe_configured": is_stripe_configured(),
        "trial_days": settings.trial_period_days,
        "grace_period_days": settings.subscription_grace_period_days,
    }
