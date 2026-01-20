"""Billing and subscription management endpoints."""

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
)
from app.crud import tenant as tenant_crud
from app.crud import user as user_crud
from app.db.session import get_db
from app.models.tenant import Tenant, SubscriptionStatus
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
)
from app.schemas.tenant import TenantCreate

router = APIRouter()


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
            max_storage_mb=plan.max_storage_mb,
            features=plan.features,
            is_popular=(plan.name == "professional"),  # Mark professional as popular
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
    
    if not plan.stripe_price_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This plan is not available for self-service signup. Please contact sales.",
        )
    
    # Create Stripe Checkout session
    display_name = signup_data.display_name or signup_data.tenant_name.replace("-", " ").title()
    
    session = await create_checkout_session(
        price_id=plan.stripe_price_id,
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
        
        # TODO: Send welcome email with password reset link
        # await send_welcome_email(email, tenant.display_name, temp_password)
        
        # TODO: Seed sample data for the new tenant
        # await seed_sample_data(db, tenant.id)
        
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
            # TODO: Send payment warning email
        
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
        
        # TODO: Send cancellation confirmation email
        
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
        
        # TODO: Send payment failed email
        
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
    
    users_count = await db.scalar(
        select(func.count(User.id)).where(User.tenant_id == tenant.id)
    ) or 0
    
    studies_count = await db.scalar(
        select(func.count(Study.id)).where(Study.tenant_id == tenant.id)
    ) or 0
    
    # Calculate limits
    max_users = plan.max_users if plan else 5
    max_studies = plan.max_studies if plan else 10
    max_storage = plan.max_storage_mb if plan else 1024
    
    # Check if unlimited (-1)
    users_remaining = -1 if max_users == -1 else max(0, max_users - users_count)
    studies_remaining = -1 if max_studies == -1 else max(0, max_studies - studies_count)
    
    subscription_info = SubscriptionInfo(
        status=tenant.subscription_status,
        plan_name=plan_name,
        plan_id=plan_id,
        trial_ends_at=tenant.trial_ends_at,
        grace_period_ends_at=tenant.grace_period_ends_at,
        cancel_at_period_end=False,  # TODO: Get from Stripe
    )
    
    usage_info = UsageInfo(
        users_count=users_count,
        users_limit=max_users,
        users_remaining=users_remaining,
        studies_count=studies_count,
        studies_limit=max_studies,
        studies_remaining=studies_remaining,
        storage_used_mb=0,  # TODO: Calculate actual storage
        storage_limit_mb=max_storage,
        storage_remaining_mb=max_storage,  # TODO: Calculate actual remaining
    )
    
    return BillingOverview(
        subscription=subscription_info,
        usage=usage_info,
        can_add_users=(max_users == -1 or users_count < max_users),
        can_add_studies=(max_studies == -1 or studies_count < max_studies),
        upgrade_available=(plan and plan.name != "enterprise"),
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
        return_url=f"{settings.frontend_url}/app/settings",
    )
    
    return BillingPortalResponse(url=session.url)


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
