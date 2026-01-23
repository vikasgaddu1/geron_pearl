"""SQLAlchemy model for ReportingEffortSignatureHistory.

This model stores an immutable audit trail of electronic signatures on reporting efforts.
Each signature event is recorded with full details for regulatory compliance.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.reporting_effort import ReportingEffort
    from app.models.user import User


class ReportingEffortSignatureHistory(Base):
    """Immutable audit trail for electronic signature events on reporting efforts."""

    __tablename__ = "reporting_effort_signature_history"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    reporting_effort_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("reporting_efforts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="The reporting effort that was signed"
    )
    signed_by_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="User who signed (preserved via username if user deleted)"
    )

    # Preserved username in case user is later deleted
    signed_by_username: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Username at time of signing (preserved for audit)"
    )

    # Signature details
    signature_hash: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        doc="SHA256:hexdigest of signature data"
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Required reason/intent for signing"
    )
    items_snapshot: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="JSON snapshot of all items at time of signing"
    )
    items_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Number of items at time of signing"
    )

    # Timestamp (timezone-aware UTC)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
        doc="When the signature was created (UTC)"
    )

    # Security audit fields
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        doc="IP address of signer (IPv4 or IPv6)"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="Browser/client user agent string"
    )

    # Relationships
    reporting_effort: Mapped["ReportingEffort"] = relationship(
        "ReportingEffort",
        back_populates="signature_history"
    )
    signed_by: Mapped[Optional["User"]] = relationship(
        "User",
        backref="signature_history_entries"
    )

    def __repr__(self) -> str:
        return (
            f"<ReportingEffortSignatureHistory("
            f"id={self.id}, "
            f"effort={self.reporting_effort_id}, "
            f"by={self.signed_by_username}, "
            f"at={self.created_at.isoformat() if self.created_at else 'None'}"
            f")>"
        )
