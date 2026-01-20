"""Subscription plan model for tiered pricing."""

from typing import TYPE_CHECKING, List, Optional, Any

from sqlalchemy import Column, Integer, String, JSON, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class SubscriptionPlan(Base, TimestampMixin):
    """
    Subscription plan model for tiered pricing.
    
    Plans define pricing tiers (Starter, Professional, Enterprise)
    with different feature limits and Stripe price IDs.
    """
    __tablename__ = "subscription_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Plan identification
    name: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        nullable=False,
        doc="Plan name (e.g., 'starter', 'professional', 'enterprise')"
    )
    display_name: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        doc="Display name (e.g., 'Starter Plan')"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500), 
        nullable=True,
        doc="Plan description"
    )
    
    # Stripe integration
    stripe_price_id: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True,
        doc="Stripe price ID for this plan"
    )
    stripe_price_id_yearly: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True,
        doc="Stripe price ID for yearly billing"
    )
    
    # Pricing (in cents)
    price_monthly: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=0,
        doc="Monthly price in cents (e.g., 9900 = $99.00)"
    )
    price_yearly: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True,
        doc="Yearly price in cents (usually discounted)"
    )
    
    # Limits (-1 means unlimited)
    max_users: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=5,
        doc="Maximum users allowed (-1 = unlimited)"
    )
    max_studies: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=10,
        doc="Maximum studies allowed (-1 = unlimited)"
    )
    max_storage_mb: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=1024,
        doc="Maximum storage in MB (-1 = unlimited)"
    )
    
    # Feature flags (JSON for flexibility)
    features: Mapped[Optional[dict]] = mapped_column(
        JSON, 
        nullable=True,
        default=dict,
        doc="Feature flags for this plan (e.g., {'api_access': true, 'priority_support': false})"
    )
    
    # Display order
    sort_order: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=0,
        doc="Sort order for display (lower = first)"
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=True,
        doc="Whether plan is available for new subscriptions"
    )
    
    # Display flags
    is_popular: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether to highlight this plan as popular/recommended"
    )
    
    # Relationships
    tenants: Mapped[List["Tenant"]] = relationship(
        "Tenant",
        back_populates="plan"
    )

    def __repr__(self) -> str:
        return f"<SubscriptionPlan(id={self.id}, name='{self.name}', price=${self.price_monthly/100:.2f}/mo)>"
    
    def has_feature(self, feature_name: str) -> bool:
        """Check if plan has a specific feature enabled."""
        if self.features is None:
            return False
        return self.features.get(feature_name, False)
    
    def is_limit_reached(self, resource: str, current_count: int) -> bool:
        """Check if a resource limit has been reached."""
        limit_map = {
            "users": self.max_users,
            "studies": self.max_studies,
            "storage_mb": self.max_storage_mb,
        }
        limit = limit_map.get(resource)
        if limit is None:
            return False
        if limit == -1:  # Unlimited
            return False
        return current_count >= limit


# Default plans to seed
DEFAULT_PLANS = [
    {
        "name": "starter",
        "display_name": "Starter",
        "description": "Perfect for small teams getting started",
        "price_monthly": 9900,  # $99/month
        "price_yearly": 99000,  # $990/year (2 months free)
        "max_users": 5,
        "max_studies": 10,
        "max_storage_mb": 1024,
        "features": {
            "email_support": True,
            "api_access": False,
            "priority_support": False,
            "sso": False,
        },
        "sort_order": 1,
    },
    {
        "name": "professional",
        "display_name": "Professional",
        "description": "For growing teams with advanced needs",
        "price_monthly": 24900,  # $249/month
        "price_yearly": 249000,  # $2490/year
        "max_users": 25,
        "max_studies": -1,  # Unlimited
        "max_storage_mb": 10240,  # 10GB
        "features": {
            "email_support": True,
            "api_access": True,
            "priority_support": True,
            "sso": False,
            "custom_branding": True,
        },
        "sort_order": 2,
        "is_popular": True,  # Highlight this plan
    },
    {
        "name": "enterprise",
        "display_name": "Enterprise",
        "description": "For large organizations with custom requirements",
        "price_monthly": 0,  # Custom pricing
        "price_yearly": 0,
        "max_users": -1,  # Unlimited
        "max_studies": -1,
        "max_storage_mb": -1,
        "features": {
            "email_support": True,
            "api_access": True,
            "priority_support": True,
            "sso": True,
            "custom_branding": True,
            "dedicated_support": True,
            "custom_integrations": True,
        },
        "sort_order": 3,
    },
]
