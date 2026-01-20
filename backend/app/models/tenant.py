"""Tenant model for multi-tenant SaaS."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.subscription_plan import SubscriptionPlan
    from app.models.tenant_settings import TenantSettings
    from app.models.user import User


class SubscriptionStatus(str, Enum):
    """Subscription status for tenant billing."""
    trialing = "trialing"
    active = "active"
    past_due = "past_due"  # 7-day grace period
    canceled = "canceled"
    unpaid = "unpaid"


class Tenant(Base, TimestampMixin):
    """
    Tenant model representing a customer organization.
    
    Each tenant has isolated data via PostgreSQL Row-Level Security (RLS).
    """
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Identification
    name: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        nullable=False, 
        index=True,
        doc="URL-safe slug for tenant (e.g., 'acme-corp')"
    )
    display_name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        doc="Human-readable tenant name (e.g., 'Acme Corporation')"
    )
    
    # Stripe integration
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String(255), 
        unique=True, 
        nullable=True,
        doc="Stripe customer ID"
    )
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True,
        doc="Stripe subscription ID"
    )
    
    # Subscription status
    subscription_status: Mapped[SubscriptionStatus] = mapped_column(
        SQLEnum(SubscriptionStatus),
        default=SubscriptionStatus.trialing,
        nullable=False,
        doc="Current subscription status"
    )
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, 
        nullable=True,
        doc="When the trial period ends"
    )
    grace_period_ends_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, 
        nullable=True,
        doc="When grace period ends for past_due status"
    )
    
    # Plan/tier
    plan_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("subscription_plans.id"),
        nullable=True,
        doc="Current subscription plan"
    )
    
    # Status flags
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        doc="Whether tenant is active"
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, 
        nullable=True,
        doc="Soft delete timestamp (data retained for 90 days)"
    )
    
    # Onboarding
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether tenant has completed onboarding wizard"
    )
    sample_data_seeded: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether sample data has been seeded for this tenant"
    )
    
    # Relationships
    plan: Mapped[Optional["SubscriptionPlan"]] = relationship(
        "SubscriptionPlan",
        back_populates="tenants"
    )
    settings: Mapped[Optional["TenantSettings"]] = relationship(
        "TenantSettings",
        back_populates="tenant",
        uselist=False,
        cascade="all, delete-orphan"
    )
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name='{self.name}', status='{self.subscription_status}')>"
    
    @property
    def is_subscription_active(self) -> bool:
        """Check if tenant has an active subscription (including trial)."""
        return self.subscription_status in (
            SubscriptionStatus.trialing,
            SubscriptionStatus.active,
            SubscriptionStatus.past_due  # Still active during grace period
        )
    
    @property
    def is_in_grace_period(self) -> bool:
        """Check if tenant is in grace period."""
        if self.subscription_status != SubscriptionStatus.past_due:
            return False
        if self.grace_period_ends_at is None:
            return False
        return datetime.utcnow() < self.grace_period_ends_at
