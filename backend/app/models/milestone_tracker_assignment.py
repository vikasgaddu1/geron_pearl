"""SQLAlchemy model for MilestoneTrackerAssignment (junction table)."""

from sqlalchemy import Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.reporting_effort_milestone import ReportingEffortMilestone
    from app.models.reporting_effort_item_tracker import ReportingEffortItemTracker


class MilestoneTrackerAssignment(Base, TimestampMixin):
    """Junction table for manual milestone-to-tracker assignments.

    This enables linking specific tracker items to milestones independently
    of subtype-based or tag-based automatic linking.
    """

    __tablename__ = "milestone_tracker_assignments"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    milestone_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("reporting_effort_milestones.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    tracker_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("reporting_effort_item_tracker.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Unique constraint to prevent duplicate assignments
    __table_args__ = (
        UniqueConstraint('milestone_id', 'tracker_id', name='uq_milestone_tracker'),
    )

    # Relationships
    milestone: Mapped["ReportingEffortMilestone"] = relationship(
        "ReportingEffortMilestone",
        back_populates="tracker_assignments"
    )

    tracker: Mapped["ReportingEffortItemTracker"] = relationship(
        "ReportingEffortItemTracker",
        back_populates="milestone_assignments"
    )

    def __repr__(self) -> str:
        return f"<MilestoneTrackerAssignment(milestone_id={self.milestone_id}, tracker_id={self.tracker_id})>"
