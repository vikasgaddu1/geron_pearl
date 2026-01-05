"""SQLAlchemy model for TrackerStatusHistory - tracks time spent in each status."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional

from app.db.base import Base


if TYPE_CHECKING:
    from app.models.reporting_effort_item_tracker import ReportingEffortItemTracker
    from app.models.user import User


class TrackerStatusHistory(Base):
    """
    Tracks status changes for reporting effort item trackers.
    
    Each row represents a period of time a tracker spent in a particular status.
    When a status changes:
    1. The previous entry for that status_field gets exited_at set to NOW()
    2. A new entry is created with entered_at = NOW()
    
    This allows for:
    - Duration tracking: exited_at - entered_at (or NOW() - entered_at if current)
    - Audit trail: who changed what and when
    - Analytics: average time in each status, bottleneck identification
    """
    
    __tablename__ = "tracker_status_history"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to tracker
    tracker_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("reporting_effort_item_tracker.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Which status field changed: 'production' or 'qc'
    status_field: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Status field: 'production' or 'qc'"
    )
    
    # The status value entered
    status_value: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="The status value (e.g., 'in_progress', 'ready_for_qc')"
    )
    
    # Timestamps for duration tracking
    entered_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        doc="When this status was entered"
    )
    
    exited_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        doc="When this status was exited (NULL if current)"
    )
    
    # Who made the change
    changed_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="User who made the status change"
    )
    
    # Relationships
    tracker: Mapped["ReportingEffortItemTracker"] = relationship(
        "ReportingEffortItemTracker",
        backref="status_history"
    )
    
    changed_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        backref="status_changes"
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_tracker_status_history_tracker_field', 'tracker_id', 'status_field'),
        Index('ix_tracker_status_history_entered_at', 'entered_at'),
        {"sqlite_autoincrement": True},
    )
    
    def __repr__(self) -> str:
        return (
            f"<TrackerStatusHistory(id={self.id}, tracker={self.tracker_id}, "
            f"field={self.status_field}, value={self.status_value}, "
            f"entered={self.entered_at}, exited={self.exited_at})>"
        )
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """
        Calculate the duration in this status in seconds.
        Returns None if still in this status (exited_at is None).
        """
        if self.exited_at is None:
            # Still in this status - calculate from now
            return (datetime.utcnow() - self.entered_at).total_seconds()
        return (self.exited_at - self.entered_at).total_seconds()
    
    @property
    def is_current(self) -> bool:
        """Check if this is the current status (not yet exited)."""
        return self.exited_at is None

