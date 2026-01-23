"""Tenant settings model for per-tenant configuration."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class TenantSettings(Base, TimestampMixin):
    """
    Tenant settings for per-tenant customization.
    
    Each tenant can have custom timezone, date format, branding, etc.
    Created eagerly alongside the Tenant.
    """
    __tablename__ = "tenant_settings"

    # Use tenant_id as primary key (one-to-one relationship)
    tenant_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("tenants.id", ondelete="CASCADE"),
        primary_key=True,
        doc="Tenant ID (also serves as primary key)"
    )
    
    # Localization
    timezone: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        default="UTC",
        doc="Tenant timezone (e.g., 'America/New_York')"
    )
    date_format: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default="YYYY-MM-DD",
        doc="Date format preference"
    )
    time_format: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default="HH:mm",
        doc="Time format preference (12h or 24h)"
    )
    
    # Branding (for Professional+ plans)
    logo_url: Mapped[Optional[str]] = mapped_column(
        String(500), 
        nullable=True,
        doc="Custom logo URL"
    )
    primary_color: Mapped[Optional[str]] = mapped_column(
        String(7), 
        nullable=True,
        doc="Primary brand color (hex, e.g., '#3B82F6')"
    )
    
    # Email settings
    notification_email: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True,
        doc="Email for system notifications (defaults to admin email)"
    )
    
    # Signature & Locking Settings
    signature_locks_effort: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="When True, signing automatically locks the effort and manual lock/unlock is hidden. "
            "When False, lock/unlock is manual and independent of signing."
    )
    
    # Note: onboarding_completed and sample_data_seeded are on the Tenant model,
    # not here, to avoid duplication and ensure single source of truth.
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="settings"
    )

    def __repr__(self) -> str:
        return f"<TenantSettings(tenant_id={self.tenant_id}, timezone='{self.timezone}')>"


# Default settings for new tenants
DEFAULT_TENANT_SETTINGS = {
    "timezone": "UTC",
    "date_format": "YYYY-MM-DD",
    "time_format": "HH:mm",
    "signature_locks_effort": True,  # By default, signing automatically locks
}
