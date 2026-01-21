"""AccessRequest model for study access requests."""

from enum import Enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, String, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin


class AccessRequestType(str, Enum):
    """Type of access being requested."""
    EDITOR = "EDITOR"
    RESPONSIBLE_USER = "RESPONSIBLE_USER"


class AccessRequestStatus(str, Enum):
    """Status of the access request."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"


if TYPE_CHECKING:
    from app.models.user import User
    from app.models.study import Study


class AccessRequest(Base, TimestampMixin):
    """Access request for study permissions.

    Users can request EDITOR role or RESPONSIBLE_USER status for studies.
    Study responsible users and admins can approve/deny these requests.

    Flow:
    1. User creates request with study_id and request_type
    2. Approvers (study responsible users or admins) see pending requests
    3. Approver approves or denies with optional reason
    4. On approval, the requested access is automatically granted
    5. Requester receives notification of outcome
    """

    __tablename__ = "access_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Who is requesting access
    requester_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User requesting access"
    )

    # What study they want access to
    study_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("studies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Study the request is for"
    )

    # Type of access requested
    request_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Type of access requested: EDITOR or RESPONSIBLE_USER"
    )

    # Current status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AccessRequestStatus.PENDING.value,
        index=True,
        doc="Current status: PENDING, APPROVED, or DENIED"
    )

    # Optional message from requester
    request_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Optional reason/message from requester explaining why they need access"
    )

    # Resolution details
    resolved_by_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="User who approved/denied the request"
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        doc="When the request was resolved"
    )
    denial_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Reason for denial (if denied)"
    )

    # Relationships
    requester: Mapped["User"] = relationship(
        "User",
        foreign_keys=[requester_id],
        backref="access_requests_made"
    )
    study: Mapped["Study"] = relationship(
        "Study",
        backref="access_requests"
    )
    resolved_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[resolved_by_id],
        backref="access_requests_resolved"
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_access_requests_status_created', 'status', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<AccessRequest(id={self.id}, requester={self.requester_id}, study={self.study_id}, type={self.request_type}, status={self.status})>"
