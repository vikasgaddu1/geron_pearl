"""Application Settings SQLAlchemy model."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class AppSettings(Base, TimestampMixin):
    """Per-tenant application settings table.

    Each tenant has their own settings row. The unique constraint on
    tenant_id ensures only one configuration exists per tenant.
    """

    __tablename__ = "app_settings"
    __table_args__ = (
        UniqueConstraint('tenant_id', name='uq_app_settings_tenant'),
        Index('ix_app_settings_tenant', 'tenant_id'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Multi-tenancy
    tenant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        doc="Tenant these settings belong to"
    )

    # Settings fields
    default_due_date_offset: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=7,
        comment="Default number of days to add when auto-setting due dates"
    )

    # Track who last updated settings
    updated_by_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", backref="app_settings")
    updated_by_user = relationship("User", foreign_keys=[updated_by_user_id])

    def __repr__(self) -> str:
        return f"<AppSettings(id={self.id}, tenant_id={self.tenant_id}, default_due_date_offset={self.default_due_date_offset})>"
