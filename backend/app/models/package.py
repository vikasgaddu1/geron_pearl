"""Package SQLAlchemy model."""

from typing import TYPE_CHECKING
from sqlalchemy import Column, Integer, String, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class Package(Base, TimestampMixin):
    """Package table model."""
    
    __tablename__ = "packages"
    
    # Composite indexes and constraints for multi-tenant queries
    __table_args__ = (
        # package_name must be unique within a tenant
        UniqueConstraint('tenant_id', 'package_name', name='uq_packages_tenant_name'),
        Index('ix_packages_tenant_created', 'tenant_id', 'created_at'),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Multi-tenancy: Each package belongs to exactly one tenant
    tenant_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant this package belongs to"
    )
    
    package_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Relationships
    package_items = relationship("PackageItem", back_populates="package")
    
    # Tenant relationship
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        backref="packages"
    )
    
    def __repr__(self) -> str:
        return f"<Package(id={self.id}, tenant_id={self.tenant_id}, package_name='{self.package_name}')>"