"""Super Admin API endpoints.

This module provides endpoints for:
- Super admin authentication (separate from tenant users)
- MFA setup and verification
- Tenant impersonation
- Platform dashboard and tenant management
"""

import logging
from datetime import datetime, timedelta
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.super_admin_security import (
    create_super_admin_token,
    create_impersonation_token,
    get_current_super_admin,
    require_mfa,
    verify_mfa_token,
    generate_mfa_secret,
    get_mfa_uri,
    generate_backup_codes,
    log_impersonation_start,
    IMPERSONATION_TOKEN_EXPIRE_MINUTES,
)
from app.crud.super_admin import super_admin as super_admin_crud
from app.crud.tenant import tenant as tenant_crud
from app.db.session import get_db
from app.models.super_admin import SuperAdmin
from app.models.tenant import Tenant, SubscriptionStatus
from app.models.user import User
from app.models.study import Study
from app.models.subscription_plan import SubscriptionPlan
from app.schemas.super_admin import (
    SuperAdminLogin,
    SuperAdminLoginResponse,
    SuperAdminCreate,
    SuperAdminRead,
    SuperAdminList,
    MFASetupResponse,
    MFAVerifyRequest,
    ImpersonationRequest,
    ImpersonationResponse,
    TenantSummary,
    TenantListResponse,
    DashboardStats,
    TenantBillingDetails,
    TenantBillingResponse,
    InvoiceSummary,
    RevenueByPlan,
    RevenueStats,
)
from app.schemas.feature_request import (
    FeatureRequestUpdate,
    FeatureRequestWithUser,
    FeatureRequestListResponse,
    FeatureRequestStatsResponse,
)
from app.crud.feature_request import feature_request as feature_request_crud
from app.models.feature_request import FeatureRequestStatus, FeatureRequestCategory

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Authentication Endpoints
# =============================================================================

@router.post("/login", response_model=SuperAdminLoginResponse)
async def login(
    login_data: SuperAdminLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Super admin login endpoint.
    
    Separate from tenant user login. Uses different JWT secret.
    """
    super_admin = await super_admin_crud.authenticate(
        db,
        email=login_data.email,
        password=login_data.password,
    )
    
    if not super_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # Check if MFA is required
    if super_admin.mfa_enabled:
        if not login_data.mfa_token:
            # Return partial response indicating MFA is required
            return SuperAdminLoginResponse(
                access_token="",
                requires_mfa=True,
                super_admin=SuperAdminRead.model_validate(super_admin),
            )
        
        # Verify MFA token
        if not verify_mfa_token(super_admin.mfa_secret, login_data.mfa_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA token",
            )
    
    # Update last login
    ip_address = request.client.host if request.client else None
    await super_admin_crud.update_last_login(db, super_admin=super_admin, ip_address=ip_address)
    
    # Create token
    access_token = create_super_admin_token(super_admin.id, super_admin.email)
    
    logger.info(f"Super admin {super_admin.email} logged in from {ip_address}")
    
    return SuperAdminLoginResponse(
        access_token=access_token,
        requires_mfa=False,
        super_admin=SuperAdminRead.model_validate(super_admin),
    )


@router.get("/me", response_model=SuperAdminRead)
async def get_me(
    super_admin: SuperAdmin = Depends(get_current_super_admin),
) -> Any:
    """Get current super admin's profile."""
    return super_admin


# =============================================================================
# MFA Endpoints
# =============================================================================

@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Set up MFA for the current super admin.
    
    Returns the secret and provisioning URI for QR code.
    """
    if super_admin.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled",
        )
    
    # Generate secret and backup codes
    secret = generate_mfa_secret()
    backup_codes = generate_backup_codes()
    provisioning_uri = get_mfa_uri(super_admin.email, secret)
    
    # Store temporarily (will be confirmed in verify endpoint)
    # For now, store encrypted in mfa_secret but don't enable yet
    super_admin.mfa_secret = secret
    super_admin.mfa_backup_codes = ",".join(backup_codes)
    await db.commit()
    
    return MFASetupResponse(
        secret=secret,
        provisioning_uri=provisioning_uri,
        backup_codes=backup_codes,
    )


@router.post("/mfa/verify")
async def verify_mfa_setup(
    verify_data: MFAVerifyRequest,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Verify MFA setup by providing a valid token.
    
    This confirms the user has correctly set up their authenticator app.
    """
    if super_admin.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled",
        )
    
    if not super_admin.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA setup not initiated. Call /mfa/setup first.",
        )
    
    if not verify_mfa_token(super_admin.mfa_secret, verify_data.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA token. Please try again.",
        )
    
    # Enable MFA
    super_admin.mfa_enabled = True
    await db.commit()
    
    logger.info(f"Super admin {super_admin.email} enabled MFA")
    
    return {"message": "MFA enabled successfully"}


@router.post("/mfa/disable")
async def disable_mfa(
    verify_data: MFAVerifyRequest,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Disable MFA (requires current MFA token for security).
    """
    if not super_admin.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled",
        )
    
    if not verify_mfa_token(super_admin.mfa_secret, verify_data.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA token",
        )
    
    await super_admin_crud.disable_mfa(db, super_admin=super_admin)
    
    logger.info(f"Super admin {super_admin.email} disabled MFA")
    
    return {"message": "MFA disabled successfully"}


# =============================================================================
# Impersonation Endpoints
# =============================================================================

@router.post("/impersonate", response_model=ImpersonationResponse)
async def impersonate_tenant(
    impersonation_data: ImpersonationRequest,
    request: Request,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Start an impersonation session for a tenant.
    
    SECURITY:
    - Creates a short-lived token (1 hour)
    - Read-only by default
    - Full audit trail
    - Cannot impersonate in production without MFA
    """
    # In production, require MFA
    if settings.env == "production" and not super_admin.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MFA must be enabled for impersonation in production",
        )
    
    # Get tenant
    tenant = await tenant_crud.get(db, id=impersonation_data.tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    
    # Get target user (default to tenant admin)
    if impersonation_data.target_user_id:
        result = await db.execute(
            select(User).where(
                User.id == impersonation_data.target_user_id,
                User.tenant_id == tenant.id,
            )
        )
        target_user = result.scalar_one_or_none()
    else:
        # Get first admin user of the tenant
        result = await db.execute(
            select(User).where(
                User.tenant_id == tenant.id,
                User.is_admin == True,
                User.is_active == True,
            ).limit(1)
        )
        target_user = result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found in tenant",
        )
    
    # Log impersonation start
    ip_address = request.client.host if request.client else None
    await log_impersonation_start(
        db,
        super_admin=super_admin,
        tenant=tenant,
        target_user_id=target_user.id,
        ip_address=ip_address,
    )
    
    # Create impersonation token
    access_token = create_impersonation_token(
        super_admin_id=super_admin.id,
        tenant_id=tenant.id,
        target_user_id=target_user.id,
        read_only=impersonation_data.read_only,
    )
    
    expires_at = datetime.utcnow() + timedelta(minutes=IMPERSONATION_TOKEN_EXPIRE_MINUTES)
    
    logger.info(
        f"Super admin {super_admin.email} started impersonation of "
        f"user {target_user.username} in tenant {tenant.name}"
    )
    
    return ImpersonationResponse(
        access_token=access_token,
        tenant_id=tenant.id,
        tenant_name=tenant.display_name,
        target_user_id=target_user.id,
        target_username=target_user.username,
        read_only=impersonation_data.read_only,
        expires_at=expires_at,
    )


@router.post("/impersonate/end")
async def end_impersonation(
    request: Request,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    End an impersonation session.
    
    This endpoint should be called by the frontend when the super admin
    clicks "Exit Impersonation". It logs the end of the session for
    audit purposes.
    
    Note: The actual impersonation token is managed by the frontend,
    so this endpoint is primarily for audit logging.
    """
    from app.core.super_admin_security import log_impersonation_end
    
    # Extract tenant_id from request if provided
    body = None
    try:
        body = await request.json()
    except Exception:
        pass
    
    tenant_id = body.get("tenant_id") if body else None
    ip_address = request.client.host if request.client else None
    
    # Log impersonation end
    if tenant_id:
        await log_impersonation_end(
            db,
            super_admin_id=super_admin.id,
            tenant_id=tenant_id,
            ip_address=ip_address,
        )
    
    logger.info(f"Super admin {super_admin.email} ended impersonation session")
    
    return {"message": "Impersonation session ended"}


# =============================================================================
# Dashboard Endpoints
# =============================================================================

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    super_admin: SuperAdmin = Depends(require_mfa),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get platform-wide statistics for the super admin dashboard."""
    # Count tenants by status
    total_tenants = await db.scalar(select(func.count(Tenant.id))) or 0
    
    active_tenants = await db.scalar(
        select(func.count(Tenant.id)).where(
            Tenant.subscription_status == SubscriptionStatus.active
        )
    ) or 0
    
    trialing_tenants = await db.scalar(
        select(func.count(Tenant.id)).where(
            Tenant.subscription_status == SubscriptionStatus.trialing
        )
    ) or 0
    
    past_due_tenants = await db.scalar(
        select(func.count(Tenant.id)).where(
            Tenant.subscription_status == SubscriptionStatus.past_due
        )
    ) or 0
    
    canceled_tenants = await db.scalar(
        select(func.count(Tenant.id)).where(
            Tenant.subscription_status == SubscriptionStatus.canceled
        )
    ) or 0
    
    # Count users and studies
    total_users = await db.scalar(select(func.count(User.id))) or 0
    total_studies = await db.scalar(select(func.count(Study.id))) or 0
    
    # Calculate MRR (simplified - sum of active subscription monthly prices)
    mrr_result = await db.execute(
        select(func.sum(SubscriptionPlan.price_monthly))
        .join(Tenant, Tenant.plan_id == SubscriptionPlan.id)
        .where(Tenant.subscription_status == SubscriptionStatus.active)
    )
    revenue_mrr = mrr_result.scalar() or 0
    
    return DashboardStats(
        total_tenants=total_tenants,
        active_tenants=active_tenants,
        trialing_tenants=trialing_tenants,
        past_due_tenants=past_due_tenants,
        canceled_tenants=canceled_tenants,
        total_users=total_users,
        total_studies=total_studies,
        revenue_mrr=revenue_mrr,
    )


@router.get("/tenants", response_model=TenantListResponse)
async def list_tenants(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    super_admin: SuperAdmin = Depends(require_mfa),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List all tenants with pagination and filtering.
    
    Requires MFA in production.
    """
    # Build query
    query = select(Tenant)
    count_query = select(func.count(Tenant.id))
    
    # Apply filters
    if status_filter:
        try:
            status_enum = SubscriptionStatus(status_filter)
            query = query.where(Tenant.subscription_status == status_enum)
            count_query = count_query.where(Tenant.subscription_status == status_enum)
        except ValueError:
            pass  # Invalid status, ignore filter
    
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (Tenant.name.ilike(search_filter)) |
            (Tenant.display_name.ilike(search_filter))
        )
        count_query = count_query.where(
            (Tenant.name.ilike(search_filter)) |
            (Tenant.display_name.ilike(search_filter))
        )
    
    # Get total count
    total = await db.scalar(count_query) or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Tenant.created_at.desc())
    
    result = await db.execute(query)
    tenants = result.scalars().all()
    
    # Build response with counts
    items = []
    for tenant in tenants:
        # Get counts for each tenant
        users_count = await db.scalar(
            select(func.count(User.id)).where(User.tenant_id == tenant.id)
        ) or 0
        
        studies_count = await db.scalar(
            select(func.count(Study.id)).where(Study.tenant_id == tenant.id)
        ) or 0
        
        # Get plan name
        plan_name = None
        if tenant.plan_id:
            plan_result = await db.execute(
                select(SubscriptionPlan.display_name)
                .where(SubscriptionPlan.id == tenant.plan_id)
            )
            plan_name = plan_result.scalar()
        
        items.append(TenantSummary(
            id=tenant.id,
            name=tenant.name,
            display_name=tenant.display_name,
            subscription_status=tenant.subscription_status.value,
            plan_name=plan_name,
            users_count=users_count,
            studies_count=studies_count,
            created_at=tenant.created_at,
            trial_ends_at=tenant.trial_ends_at,
            is_deleted=tenant.is_deleted,
        ))
    
    return TenantListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/tenants/{tenant_id}", response_model=TenantSummary)
async def get_tenant(
    tenant_id: int,
    super_admin: SuperAdmin = Depends(require_mfa),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get detailed information about a specific tenant. Requires MFA in production."""
    tenant = await tenant_crud.get(db, id=tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    
    users_count = await db.scalar(
        select(func.count(User.id)).where(User.tenant_id == tenant.id)
    ) or 0
    
    studies_count = await db.scalar(
        select(func.count(Study.id)).where(Study.tenant_id == tenant.id)
    ) or 0
    
    plan_name = None
    if tenant.plan_id:
        plan_result = await db.execute(
            select(SubscriptionPlan.display_name)
            .where(SubscriptionPlan.id == tenant.plan_id)
        )
        plan_name = plan_result.scalar()
    
    return TenantSummary(
        id=tenant.id,
        name=tenant.name,
        display_name=tenant.display_name,
        subscription_status=tenant.subscription_status.value,
        plan_name=plan_name,
        users_count=users_count,
        studies_count=studies_count,
        created_at=tenant.created_at,
        trial_ends_at=tenant.trial_ends_at,
        is_deleted=tenant.is_deleted,
    )


# =============================================================================
# Billing Management Endpoints
# =============================================================================

@router.get("/tenants/{tenant_id}/billing", response_model=TenantBillingResponse)
async def get_tenant_billing(
    tenant_id: int,
    super_admin: SuperAdmin = Depends(require_mfa),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get detailed billing information for a tenant.

    Includes Stripe subscription details and recent invoices.
    Requires MFA in production.
    """
    from app.core.stripe import (
        get_subscription_details,
        get_customer_invoices,
        get_stripe_dashboard_url,
        is_stripe_configured,
    )
    from app.schemas.super_admin import (
        TenantBillingDetails,
        InvoiceSummary,
        TenantBillingResponse,
    )

    tenant = await tenant_crud.get(db, id=tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    # Get user/study counts
    users_count = await db.scalar(
        select(func.count(User.id)).where(User.tenant_id == tenant.id)
    ) or 0
    studies_count = await db.scalar(
        select(func.count(Study.id)).where(Study.tenant_id == tenant.id)
    ) or 0

    # Get plan info
    plan_name = None
    users_limit = 5  # Default starter limits
    studies_limit = 10
    if tenant.plan_id:
        plan_result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == tenant.plan_id)
        )
        plan = plan_result.scalar_one_or_none()
        if plan:
            plan_name = plan.display_name
            users_limit = plan.max_users
            studies_limit = plan.max_studies

    # Get Stripe details
    stripe_dashboard_url = None
    current_period_start = None
    current_period_end = None
    cancel_at_period_end = False
    invoices = []

    if is_stripe_configured() and tenant.stripe_customer_id:
        stripe_dashboard_url = get_stripe_dashboard_url(tenant.stripe_customer_id)

        if tenant.stripe_subscription_id:
            sub_details = await get_subscription_details(tenant.stripe_subscription_id)
            if sub_details:
                current_period_start = datetime.fromtimestamp(sub_details["current_period_start"])
                current_period_end = datetime.fromtimestamp(sub_details["current_period_end"])
                cancel_at_period_end = sub_details.get("cancel_at_period_end", False)

        # Get invoices
        raw_invoices = await get_customer_invoices(tenant.stripe_customer_id, limit=10)
        for inv in raw_invoices:
            paid_at = None
            if hasattr(inv, 'status_transitions') and inv.status_transitions:
                if hasattr(inv.status_transitions, 'paid_at') and inv.status_transitions.paid_at:
                    paid_at = datetime.fromtimestamp(inv.status_transitions.paid_at)

            invoices.append(InvoiceSummary(
                id=inv.id,
                number=inv.number,
                status=inv.status,
                amount_due=inv.amount_due,
                amount_paid=inv.amount_paid,
                currency=inv.currency,
                created=datetime.fromtimestamp(inv.created),
                due_date=datetime.fromtimestamp(inv.due_date) if inv.due_date else None,
                paid_at=paid_at,
                invoice_pdf=inv.invoice_pdf,
                hosted_invoice_url=inv.hosted_invoice_url,
            ))

    return TenantBillingResponse(
        tenant=TenantBillingDetails(
            id=tenant.id,
            name=tenant.name,
            display_name=tenant.display_name,
            created_at=tenant.created_at,
            stripe_customer_id=tenant.stripe_customer_id,
            stripe_subscription_id=tenant.stripe_subscription_id,
            stripe_dashboard_url=stripe_dashboard_url,
            subscription_status=tenant.subscription_status.value,
            plan_name=plan_name,
            plan_id=tenant.plan_id,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            cancel_at_period_end=cancel_at_period_end,
            trial_ends_at=tenant.trial_ends_at,
            grace_period_ends_at=tenant.grace_period_ends_at,
            users_count=users_count,
            users_limit=users_limit,
            studies_count=studies_count,
            studies_limit=studies_limit,
        ),
        invoices=invoices,
    )


@router.get("/revenue/breakdown", response_model=RevenueStats)
async def get_revenue_breakdown(
    super_admin: SuperAdmin = Depends(require_mfa),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get revenue breakdown by plan and conversion metrics.

    Requires MFA in production.
    """
    from app.schemas.super_admin import RevenueByPlan, RevenueStats

    # Get MRR by plan for active tenants
    result = await db.execute(
        select(
            SubscriptionPlan.id,
            SubscriptionPlan.display_name,
            SubscriptionPlan.price_monthly,
            func.count(Tenant.id).label("tenant_count")
        )
        .join(Tenant, Tenant.plan_id == SubscriptionPlan.id)
        .where(Tenant.subscription_status == SubscriptionStatus.active)
        .group_by(SubscriptionPlan.id, SubscriptionPlan.display_name, SubscriptionPlan.price_monthly)
    )

    by_plan = []
    total_mrr = 0
    for row in result:
        mrr = row.price_monthly * row.tenant_count
        total_mrr += mrr
        by_plan.append(RevenueByPlan(
            plan_name=row.display_name,
            plan_id=row.id,
            tenant_count=row.tenant_count,
            mrr=mrr,
        ))

    # Trial count
    trial_count = await db.scalar(
        select(func.count(Tenant.id)).where(
            Tenant.subscription_status == SubscriptionStatus.trialing
        )
    ) or 0

    # Churned in last 30 days (count canceled tenants updated in last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    churned_count = await db.scalar(
        select(func.count(Tenant.id)).where(
            Tenant.subscription_status == SubscriptionStatus.canceled,
            Tenant.updated_at >= thirty_days_ago
        )
    ) or 0

    return RevenueStats(
        total_mrr=total_mrr,
        by_plan=by_plan,
        trial_count=trial_count,
        trial_conversion_rate=None,  # Would need historical data to calculate
        churned_last_30_days=churned_count,
    )


# =============================================================================
# Feature Request Management Endpoints
# =============================================================================

@router.get("/feature-requests", response_model=FeatureRequestListResponse)
async def list_feature_requests(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    super_admin: SuperAdmin = Depends(require_mfa),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List all feature requests across all tenants.

    Supports filtering by status (pending, working, done) and category (bug, feature).
    Requires MFA in production.
    """
    # Parse filters
    req_status = None
    if status_filter:
        try:
            req_status = FeatureRequestStatus(status_filter)
        except ValueError:
            pass

    category = None
    if category_filter:
        try:
            category = FeatureRequestCategory(category_filter)
        except ValueError:
            pass

    items = await feature_request_crud.get_all_requests(
        db,
        status=req_status,
        category=category,
        skip=skip,
        limit=limit
    )

    total = await feature_request_crud.get_total_count(
        db,
        status=req_status,
        category=category
    )

    return FeatureRequestListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/feature-requests/stats", response_model=FeatureRequestStatsResponse)
async def get_feature_request_stats(
    super_admin: SuperAdmin = Depends(require_mfa),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get counts of feature requests by status.

    Returns counts for pending, working, and done statuses.
    Requires MFA in production.
    """
    return await feature_request_crud.get_stats(db)


@router.get("/feature-requests/{request_id}", response_model=FeatureRequestWithUser)
async def get_feature_request_detail(
    request_id: int,
    super_admin: SuperAdmin = Depends(require_mfa),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get detailed information about a specific feature request.

    Includes user and tenant information.
    Requires MFA in production.
    """
    result = await feature_request_crud.get_request_with_user(db, request_id=request_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature request not found",
        )

    return result


@router.put("/feature-requests/{request_id}", response_model=FeatureRequestWithUser)
async def update_feature_request(
    request_id: int,
    update_data: FeatureRequestUpdate,
    super_admin: SuperAdmin = Depends(require_mfa),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a feature request status and/or admin response.

    Used for Kanban board drag-and-drop status changes and adding responses.
    Requires MFA in production.
    """
    result = await feature_request_crud.update_request(
        db,
        request_id=request_id,
        obj_in=update_data
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature request not found",
        )

    # Get full details with user info
    return await feature_request_crud.get_request_with_user(db, request_id=request_id)
