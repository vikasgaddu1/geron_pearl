"""Pydantic schemas for Tenant."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.tenant import SubscriptionStatus


class TenantBase(BaseModel):
    """Base schema for Tenant."""
    name: str = Field(..., min_length=1, max_length=255, description="URL-safe tenant slug")
    display_name: str = Field(..., min_length=1, max_length=255, description="Human-readable tenant name")


class TenantCreate(TenantBase):
    """Schema for creating a new tenant."""
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    subscription_status: Optional[SubscriptionStatus] = SubscriptionStatus.trialing
    trial_ends_at: Optional[datetime] = None
    plan_id: Optional[int] = None


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    subscription_status: Optional[SubscriptionStatus] = None
    trial_ends_at: Optional[datetime] = None
    grace_period_ends_at: Optional[datetime] = None
    plan_id: Optional[int] = None
    is_active: Optional[bool] = None


class TenantResponse(TenantBase):
    """Schema for tenant response."""
    id: int
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    subscription_status: SubscriptionStatus
    trial_ends_at: Optional[datetime] = None
    grace_period_ends_at: Optional[datetime] = None
    plan_id: Optional[int] = None
    is_active: bool
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class TenantWithStats(TenantResponse):
    """Schema for tenant with usage statistics."""
    user_count: int = 0
    study_count: int = 0
    storage_used_mb: int = 0


# Subscription Plan schemas
class SubscriptionPlanBase(BaseModel):
    """Base schema for SubscriptionPlan."""
    name: str
    display_name: str
    description: Optional[str] = None
    price_monthly: int = Field(default=0, description="Price in cents")
    price_yearly: Optional[int] = None


class SubscriptionPlanCreate(SubscriptionPlanBase):
    """Schema for creating a subscription plan."""
    stripe_price_id: Optional[str] = None
    stripe_price_id_yearly: Optional[str] = None
    max_users: int = 5
    max_studies: int = 10
    max_storage_mb: int = 1024
    features: Optional[dict] = None
    sort_order: int = 0


class SubscriptionPlanResponse(SubscriptionPlanBase):
    """Schema for subscription plan response."""
    id: int
    stripe_price_id: Optional[str] = None
    stripe_price_id_yearly: Optional[str] = None
    max_users: int
    max_studies: int
    max_storage_mb: int
    features: Optional[dict] = None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Tenant Settings schemas
class TenantSettingsBase(BaseModel):
    """Base schema for TenantSettings."""
    timezone: str = "UTC"
    date_format: str = "YYYY-MM-DD"
    time_format: str = "HH:mm"
    signature_locks_effort: bool = True  # Default: signing auto-locks


class TenantSettingsUpdate(BaseModel):
    """Schema for updating tenant settings."""
    timezone: Optional[str] = None
    date_format: Optional[str] = None
    time_format: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    notification_email: Optional[str] = None
    onboarding_completed: Optional[bool] = None
    signature_locks_effort: Optional[bool] = None


class TenantSettingsResponse(TenantSettingsBase):
    """Schema for tenant settings response."""
    tenant_id: int
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    notification_email: Optional[str] = None
    onboarding_completed: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
