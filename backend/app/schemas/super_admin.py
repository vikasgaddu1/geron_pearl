"""Pydantic schemas for Super Admin."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# =============================================================================
# Authentication Schemas
# =============================================================================

class SuperAdminLogin(BaseModel):
    """Login request for super admin."""
    email: str = Field(..., min_length=1, max_length=255, description="Super admin email address")
    password: str = Field(..., min_length=8)
    mfa_token: Optional[str] = Field(None, description="MFA token if MFA is enabled")


class SuperAdminLoginResponse(BaseModel):
    """Login response with token."""
    access_token: str
    token_type: str = "bearer"
    requires_mfa: bool = False
    super_admin: "SuperAdminRead"


class MFASetupResponse(BaseModel):
    """Response when setting up MFA."""
    secret: str
    provisioning_uri: str
    backup_codes: List[str]


class MFAVerifyRequest(BaseModel):
    """Request to verify MFA setup or login."""
    token: str = Field(..., min_length=6, max_length=6)


# =============================================================================
# Impersonation Schemas
# =============================================================================

class ImpersonationRequest(BaseModel):
    """Request to impersonate a tenant user."""
    tenant_id: int
    target_user_id: Optional[int] = Field(
        None, 
        description="User to impersonate (defaults to tenant admin)"
    )
    read_only: bool = Field(
        True, 
        description="If true, mutations are blocked"
    )


class ImpersonationResponse(BaseModel):
    """Response with impersonation token."""
    access_token: str
    token_type: str = "bearer"
    tenant_id: int
    tenant_name: str
    target_user_id: int
    target_username: str
    read_only: bool
    expires_at: datetime


# =============================================================================
# Super Admin CRUD Schemas
# =============================================================================

class SuperAdminCreate(BaseModel):
    """Schema for creating a super admin."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2, max_length=255)


class SuperAdminUpdate(BaseModel):
    """Schema for updating a super admin."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    is_active: Optional[bool] = None


class SuperAdminRead(BaseModel):
    """Schema for reading a super admin."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: str
    name: str
    is_active: bool
    mfa_enabled: bool
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class SuperAdminList(BaseModel):
    """List of super admins."""
    items: List[SuperAdminRead]
    total: int


# =============================================================================
# Tenant Management Schemas (for Super Admin Dashboard)
# =============================================================================

class TenantSummary(BaseModel):
    """Summary of a tenant for the super admin dashboard."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    display_name: str
    subscription_status: str
    plan_name: Optional[str] = None
    users_count: int
    studies_count: int
    created_at: datetime
    trial_ends_at: Optional[datetime] = None
    is_deleted: bool


class TenantListResponse(BaseModel):
    """List of tenants with pagination."""
    items: List[TenantSummary]
    total: int
    page: int
    page_size: int


class DashboardStats(BaseModel):
    """Dashboard statistics for super admin."""
    total_tenants: int
    active_tenants: int
    trialing_tenants: int
    past_due_tenants: int
    canceled_tenants: int
    total_users: int
    total_studies: int
    revenue_mrr: int  # Monthly recurring revenue in cents


# =============================================================================
# Billing Management Schemas (for Super Admin)
# =============================================================================

class TenantBillingDetails(BaseModel):
    """Extended billing details for a tenant."""
    model_config = ConfigDict(from_attributes=True)

    # Basic tenant info
    id: int
    name: str
    display_name: str
    created_at: datetime

    # Stripe identifiers
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    stripe_dashboard_url: Optional[str] = None

    # Subscription details
    subscription_status: str
    plan_name: Optional[str] = None
    plan_id: Optional[int] = None

    # Billing period (from Stripe)
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False

    # Trial/Grace
    trial_ends_at: Optional[datetime] = None
    grace_period_ends_at: Optional[datetime] = None

    # Usage
    users_count: int
    users_limit: int  # -1 = unlimited
    studies_count: int
    studies_limit: int  # -1 = unlimited


class InvoiceSummary(BaseModel):
    """Summary of a Stripe invoice."""
    id: str
    number: Optional[str] = None
    status: str  # draft, open, paid, void, uncollectible
    amount_due: int  # in cents
    amount_paid: int  # in cents
    currency: str
    created: datetime
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    invoice_pdf: Optional[str] = None
    hosted_invoice_url: Optional[str] = None


class TenantBillingResponse(BaseModel):
    """Full billing response for a tenant."""
    tenant: TenantBillingDetails
    invoices: List[InvoiceSummary]


class RevenueByPlan(BaseModel):
    """Revenue breakdown by plan."""
    plan_name: str
    plan_id: int
    tenant_count: int
    mrr: int  # Monthly recurring revenue in cents


class RevenueStats(BaseModel):
    """Extended revenue statistics for platform."""
    total_mrr: int
    by_plan: List[RevenueByPlan]
    trial_count: int
    trial_conversion_rate: Optional[float] = None  # percentage (0-100)
    churned_last_30_days: int


# Forward references
SuperAdminLoginResponse.model_rebuild()
