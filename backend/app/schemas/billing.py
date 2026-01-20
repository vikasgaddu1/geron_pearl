"""Pydantic schemas for billing and Stripe integration."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, EmailStr

from app.models.tenant import SubscriptionStatus


class SignupInitiate(BaseModel):
    """Schema for initiating signup before Stripe checkout."""
    tenant_name: str = Field(
        ..., 
        min_length=3, 
        max_length=50, 
        pattern=r'^[a-z0-9][a-z0-9-]*[a-z0-9]$',
        description="URL-safe tenant slug (lowercase letters, numbers, hyphens)"
    )
    email: EmailStr = Field(..., description="Admin email for the tenant")
    plan_id: int = Field(..., description="Subscription plan ID")
    display_name: Optional[str] = Field(None, max_length=255, description="Human-readable tenant name")


class SignupInitiateResponse(BaseModel):
    """Response after initiating signup."""
    checkout_url: str = Field(..., description="Stripe Checkout URL to redirect user to")
    session_id: str = Field(..., description="Stripe Checkout session ID")


class CheckoutSessionCreate(BaseModel):
    """Schema for creating a checkout session for existing tenant (upgrade/change plan)."""
    plan_id: int
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class BillingPortalResponse(BaseModel):
    """Response for billing portal redirect."""
    url: str = Field(..., description="Stripe Billing Portal URL")


class SubscriptionInfo(BaseModel):
    """Current subscription information."""
    status: SubscriptionStatus
    plan_name: str
    plan_id: int
    current_period_end: Optional[datetime] = None
    trial_ends_at: Optional[datetime] = None
    grace_period_ends_at: Optional[datetime] = None
    cancel_at_period_end: bool = False
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class UsageInfo(BaseModel):
    """Current usage information for the tenant."""
    users_count: int
    users_limit: int
    users_remaining: int
    studies_count: int
    studies_limit: int
    studies_remaining: int
    storage_used_mb: int
    storage_limit_mb: int
    storage_remaining_mb: int


class BillingOverview(BaseModel):
    """Complete billing overview for tenant dashboard."""
    subscription: SubscriptionInfo
    usage: UsageInfo
    can_add_users: bool
    can_add_studies: bool
    upgrade_available: bool


class PlanInfo(BaseModel):
    """Public plan information for pricing page."""
    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    price_monthly: int = Field(..., description="Price in cents")
    price_yearly: Optional[int] = Field(None, description="Yearly price in cents (if available)")
    max_users: int
    max_studies: int
    max_storage_mb: int
    features: Optional[dict] = None
    is_popular: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class PlanListResponse(BaseModel):
    """List of available plans."""
    plans: List[PlanInfo]


class WebhookEvent(BaseModel):
    """Stripe webhook event (for logging/debugging)."""
    event_id: str
    event_type: str
    processed_at: datetime
    tenant_id: Optional[int] = None
    success: bool
    error_message: Optional[str] = None
