"""Pydantic schemas for Super Admin."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# =============================================================================
# Authentication Schemas
# =============================================================================

class SuperAdminLogin(BaseModel):
    """Login request for super admin."""
    email: EmailStr
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


# Forward references
SuperAdminLoginResponse.model_rebuild()
