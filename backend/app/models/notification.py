"""SQLAlchemy model for Notification."""

from enum import Enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class NotificationType(str, Enum):
    """Notification type enum."""
    ASSIGNMENT_PROD = "assignment_prod"  # Assigned as production programmer
    ASSIGNMENT_QC = "assignment_qc"      # Assigned as QC programmer
    ASSIGNMENT_BIOSTAT = "assignment_biostat"  # Assigned as biostat reviewer
    COMMENT_ADDED = "comment_added"      # New comment on item user is assigned to
    BIOSTAT_FAILED = "biostat_failed"    # Biostat reviewer failed the item


if TYPE_CHECKING:
    from app.models.user import User
    from app.models.tenant import Tenant
    from app.models.reporting_effort_item_tracker import ReportingEffortItemTracker


class Notification(Base):
    """User notification model for assignments and comments."""
    
    __tablename__ = "notifications"
    
    # Composite indexes for multi-tenant queries
    __table_args__ = (
        Index('ix_notifications_tenant_user', 'tenant_id', 'user_id'),
        Index('ix_notifications_tenant_unread', 'tenant_id', 'user_id', 'is_read'),
    )
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Multi-tenancy
    tenant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant this notification belongs to"
    )
    
    # Foreign keys
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="The user who should receive this notification"
    )
    tracker_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("reporting_effort_item_tracker.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="The tracker item this notification relates to"
    )
    triggered_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="The user who triggered this notification (e.g., who assigned or commented)"
    )
    
    # Notification fields
    notification_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Type of notification: assignment_prod, assignment_qc, comment_added"
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Short title for the notification"
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Detailed notification message"
    )
    
    # Context fields for navigation
    item_code: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Item code for display and navigation"
    )
    study_label: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        doc="Study label for context"
    )
    
    # Status
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether the user has seen this notification"
    )
    is_acknowledged: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether the user has dismissed this notification"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        doc="When the notification was created"
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        doc="When the notification was marked as read"
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        doc="When the notification was acknowledged/dismissed"
    )
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", backref="notifications")
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        backref="notifications"
    )
    triggered_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[triggered_by_user_id]
    )
    tracker: Mapped[Optional["ReportingEffortItemTracker"]] = relationship(
        "ReportingEffortItemTracker",
        backref="notifications"
    )
    
    def __repr__(self) -> str:
        try:
            return f"<Notification(id={self.id}, user={self.user_id}, type={self.notification_type}, read={self.is_read})>"
        except Exception:
            return "<Notification(detached)>"
