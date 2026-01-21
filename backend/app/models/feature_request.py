"""SQLAlchemy model for Feature Request / Bug Report."""

from enum import Enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FeatureRequestStatus(str, Enum):
    """Feature request status enum."""
    PENDING = "pending"    # New, awaiting review
    WORKING = "working"    # Being worked on
    DONE = "done"          # Completed


class FeatureRequestCategory(str, Enum):
    """Feature request category enum."""
    BUG = "bug"            # Bug report
    FEATURE = "feature"    # Feature request


if TYPE_CHECKING:
    from app.models.user import User
    from app.models.tenant import Tenant


class FeatureRequest(Base):
    """Feature request / bug report model for tenant user feedback."""

    __tablename__ = "feature_requests"

    # Composite indexes for efficient queries
    __table_args__ = (
        Index('ix_feature_requests_tenant_status', 'tenant_id', 'status'),
        Index('ix_feature_requests_tenant_user', 'tenant_id', 'user_id'),
        Index('ix_feature_requests_status', 'status'),
    )

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Multi-tenancy
    tenant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant this request belongs to"
    )

    # User who submitted
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User who submitted this request"
    )

    # Request fields
    category: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        doc="Category: bug or feature"
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Short title for the request"
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Detailed description of the request"
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20),
        default=FeatureRequestStatus.PENDING.value,
        nullable=False,
        index=True,
        doc="Status: pending, working, done"
    )

    # Admin response (visible to users)
    admin_response: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Admin response visible to the user"
    )
    responded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        doc="When admin responded"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        doc="When the request was created"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        doc="When the request was last updated"
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", backref="feature_requests")
    user: Mapped["User"] = relationship("User", backref="feature_requests")

    def __repr__(self) -> str:
        try:
            return f"<FeatureRequest(id={self.id}, category={self.category}, status={self.status})>"
        except Exception:
            return "<FeatureRequest(detached)>"
