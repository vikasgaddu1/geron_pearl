"""SQLAlchemy model for AuditLog."""

from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional
from datetime import datetime

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.tenant import Tenant


class AuditLog(Base):
    """Audit log for tracking all changes in the system."""
    
    __tablename__ = "audit_log"
    
    # Composite indexes for multi-tenant queries
    __table_args__ = (
        Index('ix_audit_log_tenant_created', 'tenant_id', 'created_at'),
        Index('ix_audit_log_tenant_table', 'tenant_id', 'table_name'),
    )
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Multi-tenancy: Each audit log belongs to exactly one tenant
    tenant_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant this audit log belongs to"
    )
    
    # Audit fields
    table_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Name of the table that was modified"
    )
    record_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        doc="ID of the record that was modified"
    )
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Action performed: CREATE, UPDATE, DELETE"
    )
    
    # User tracking
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
        doc="User who performed the action"
    )
    
    # Change details
    changes_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON representation of the changes made"
    )
    
    # Request metadata
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        doc="IP address of the user"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="User agent string from the request"
    )
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        doc="When the action was performed"
    )
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        backref="audit_logs"
    )
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        backref="audit_logs"
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, tenant_id={self.tenant_id}, table={self.table_name}, record={self.record_id}, action={self.action})>"