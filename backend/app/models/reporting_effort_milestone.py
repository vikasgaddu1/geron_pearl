"""SQLAlchemy model for ReportingEffortMilestone."""

from sqlalchemy import Integer, String, ForeignKey, Date, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional, List
from datetime import date

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.reporting_effort_phase import ReportingEffortPhase
    from app.models.milestone_tracker_assignment import MilestoneTrackerAssignment
    from app.models.tracker_tag import TrackerTag


class ReportingEffortMilestone(Base, TimestampMixin):
    """Milestone model representing a task/deliverable within a phase.
    
    Examples: 'Deliver all SDTMs', 'Sponsor provides review comments'
    """
    
    __tablename__ = "reporting_effort_milestones"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    phase_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("reporting_effort_phases.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    # Data fields
    name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Milestone name/description"
    )
    start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        index=True,
        doc="Start date for this milestone"
    )
    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        doc="Target due date for this milestone"
    )
    responsibility: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True,
        doc="Party responsible (e.g., 'Tigermed', 'Geron', 'PXL')"
    )
    comments: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        doc="Additional notes or comments"
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=False,
        doc="Whether this milestone has been completed"
    )
    completion_date: Mapped[Optional[date]] = mapped_column(
        Date, 
        nullable=True,
        doc="Actual completion date"
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Order in which milestones are displayed within a phase"
    )

    # Tracker linking fields
    linked_subtype: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Item subtype to auto-link: Table, Listing, Figure, SDTM, ADaM (null = no auto-linking)"
    )

    linked_tag_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("tracker_tags.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Tag ID to auto-link: all tracker items with this tag are linked (null = no tag linking)"
    )

    # Relationships
    phase: Mapped["ReportingEffortPhase"] = relationship(
        "ReportingEffortPhase",
        back_populates="milestones"
    )

    linked_tag: Mapped[Optional["TrackerTag"]] = relationship(
        "TrackerTag",
        foreign_keys=[linked_tag_id],
        lazy="joined"
    )

    tracker_assignments: Mapped[List["MilestoneTrackerAssignment"]] = relationship(
        "MilestoneTrackerAssignment",
        back_populates="milestone",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<ReportingEffortMilestone(id={self.id}, name='{self.name[:30]}...', due_date={self.due_date})>"






