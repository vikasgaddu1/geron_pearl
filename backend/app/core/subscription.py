"""Subscription access control for multi-tenant SaaS.

This module provides dependencies and utilities to check subscription status
before allowing access to protected resources.
"""

from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.tenant import Tenant, SubscriptionStatus
from app.models.user import User


async def get_tenant_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Tenant:
    """
    Get the current user's tenant with subscription info.
    
    Returns the tenant object for further checks.
    """
    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    
    return tenant


async def require_active_subscription(
    tenant: Tenant = Depends(get_tenant_subscription),
) -> Tenant:
    """
    Dependency that requires an active subscription.
    
    Blocks access if:
    - Subscription is canceled
    - Subscription is unpaid
    - Grace period has expired for past_due status
    
    Allows access with warning header if:
    - Subscription is trialing
    - Subscription is past_due but within grace period
    """
    now = datetime.utcnow()
    
    # Check subscription status
    if tenant.subscription_status == SubscriptionStatus.canceled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your subscription has been canceled. Please resubscribe to continue using PEARL.",
            headers={"X-Subscription-Status": "canceled"},
        )
    
    if tenant.subscription_status == SubscriptionStatus.unpaid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your payment is overdue. Please update your payment method to continue.",
            headers={"X-Subscription-Status": "unpaid"},
        )
    
    if tenant.subscription_status == SubscriptionStatus.past_due:
        # Check if grace period has expired
        if tenant.grace_period_ends_at and now > tenant.grace_period_ends_at:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your grace period has expired. Please update your payment method to continue.",
                headers={"X-Subscription-Status": "past_due_expired"},
            )
        # Allow access but mark as past_due (frontend can show warning)
    
    if tenant.subscription_status == SubscriptionStatus.trialing:
        # Check if trial has expired
        if tenant.trial_ends_at and now > tenant.trial_ends_at:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your free trial has ended. Please subscribe to continue using PEARL.",
                headers={"X-Subscription-Status": "trial_expired"},
            )
    
    return tenant


async def check_user_limit(
    tenant: Tenant = Depends(get_tenant_subscription),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Check if tenant can add more users based on their plan.

    Use this dependency before creating new users.
    """
    from app.models.subscription_plan import SubscriptionPlan
    from sqlalchemy import func

    # If no plan is assigned, allow access (no limits)
    if not tenant.plan_id:
        return

    # Get plan limits
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.id == tenant.plan_id)
    )
    plan = result.scalar_one_or_none()

    # If plan not found, allow access (no limits)
    if not plan:
        return

    # Check if unlimited
    if plan.max_users == -1:
        return
    
    # Count current users
    current_count = await db.scalar(
        select(func.count(User.id)).where(User.tenant_id == tenant.id)
    ) or 0
    
    if current_count >= plan.max_users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You have reached your plan limit of {plan.max_users} users. "
                   f"Please upgrade your plan to add more users.",
            headers={"X-Limit-Reached": "users"},
        )


async def check_study_limit(
    tenant: Tenant = Depends(get_tenant_subscription),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Check if tenant can add more studies based on their plan.

    Use this dependency before creating new studies.
    """
    from app.models.subscription_plan import SubscriptionPlan
    from app.models.study import Study
    from sqlalchemy import func

    # If no plan is assigned, allow access (no limits)
    if not tenant.plan_id:
        return

    # Get plan limits
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.id == tenant.plan_id)
    )
    plan = result.scalar_one_or_none()

    # If plan not found, allow access (no limits)
    if not plan:
        return

    # Check if unlimited
    if plan.max_studies == -1:
        return
    
    # Count current studies
    current_count = await db.scalar(
        select(func.count(Study.id)).where(Study.tenant_id == tenant.id)
    ) or 0
    
    if current_count >= plan.max_studies:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You have reached your plan limit of {plan.max_studies} studies. "
                   f"Please upgrade your plan to add more studies.",
            headers={"X-Limit-Reached": "studies"},
        )


def get_subscription_warning_headers(tenant: Tenant) -> dict:
    """
    Generate warning headers based on subscription status.
    
    Can be used to add headers to responses so frontend can show warnings.
    """
    headers = {}
    now = datetime.utcnow()
    
    if tenant.subscription_status == SubscriptionStatus.trialing:
        if tenant.trial_ends_at:
            days_left = (tenant.trial_ends_at - now).days
            if days_left <= 7:
                headers["X-Trial-Days-Remaining"] = str(max(0, days_left))
    
    elif tenant.subscription_status == SubscriptionStatus.past_due:
        headers["X-Payment-Past-Due"] = "true"
        if tenant.grace_period_ends_at:
            days_left = (tenant.grace_period_ends_at - now).days
            headers["X-Grace-Period-Days-Remaining"] = str(max(0, days_left))
    
    return headers


class SubscriptionMiddleware:
    """
    Middleware to add subscription status headers to responses.
    
    This allows the frontend to show warnings about trial ending,
    payment issues, etc.
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Process request normally
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # We could add subscription headers here if we had tenant context
                # For now, the individual endpoints handle this
                pass
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
