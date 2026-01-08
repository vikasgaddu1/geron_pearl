"""StudyTeamAssignment model for tracking team member allocation to studies.

This model supports:
- Multiple allocation records per user/study (history tracking)
- Allocation percentage and productive time factors
- Experience levels with multipliers for estimation
- Effective date ranges for tracking allocation changes over time
"""

from enum import Enum
from datetime import date
from sqlalchemy import Integer, String, ForeignKey, Date, Boolean, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional

from app.db.base import Base
from app.db.mixins import TimestampMixin


if TYPE_CHECKING:
    from app.models.user import User
    from app.models.study import Study


class JobType(str, Enum):
    """Job types for team members on a study."""
    LEAD = "LEAD"
    PRODUCTION_PROGRAMMER = "PRODUCTION_PROGRAMMER"
    QC_PROGRAMMER = "QC_PROGRAMMER"


class ExperienceLevel(str, Enum):
    """Experience levels affecting estimation multipliers.
    
    Multipliers:
    - JUNIOR: 1.5 (takes 50% longer than baseline)
    - MID: 1.0 (baseline)
    - SENIOR: 0.75 (25% faster than baseline)
    """
    JUNIOR = "JUNIOR"
    MID = "MID"
    SENIOR = "SENIOR"


# Experience multipliers for estimation calculations
EXPERIENCE_MULTIPLIERS = {
    ExperienceLevel.JUNIOR: 1.5,
    ExperienceLevel.MID: 1.0,
    ExperienceLevel.SENIOR: 0.75,
}


class DepartureReason(str, Enum):
    """Reasons for ending a team assignment."""
    ALLOCATION_CHANGED = "allocation_changed"
    REASSIGNED_FULLY = "reassigned_fully"
    LEFT_ORGANIZATION = "left_organization"
    PROJECT_ENDED = "project_ended"
    OTHER = "other"


class StudyTeamAssignment(Base, TimestampMixin):
    """Tracks team member allocation to studies over time.
    
    Each record represents a period of allocation for a user on a study.
    When allocation changes (e.g., 100% -> 50%), the current record is closed
    (effective_end_date set) and a new record is created.
    
    This preserves full history of:
    - Who worked on what study
    - Their allocation percentage over time
    - When they joined/left
    - Why they left (departure reason)
    
    For capacity calculations:
    - Only records with is_active=True and effective_end_date=NULL are counted
    - Departed members' velocity history is retained for analytics
    """
    
    __tablename__ = "study_team_assignments"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    study_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("studies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Job role and allocation
    job_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Job type: LEAD, PRODUCTION_PROGRAMMER, QC_PROGRAMMER"
    )
    allocation_percentage: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False,
        doc="Percentage of time allocated to this study (1-100)"
    )
    productive_time_factor: Mapped[int] = mapped_column(
        Integer,
        default=75,
        nullable=False,
        doc="Percentage of allocated time that is trackable/productive work (typically 75-80%)"
    )
    experience_level: Mapped[str] = mapped_column(
        String(20),
        default="MID",
        nullable=False,
        doc="Experience level: JUNIOR, MID, SENIOR"
    )
    
    # Effective date range
    effective_start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date this allocation became effective"
    )
    effective_end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        doc="Date this allocation ended (NULL = still active)"
    )
    
    # Status tracking
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether this assignment is currently active"
    )
    departure_reason: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Reason for ending assignment: allocation_changed, reassigned_fully, left_organization, etc."
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Optional notes about this assignment or change"
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        backref="team_assignments"
    )
    study: Mapped["Study"] = relationship(
        "Study",
        backref="team_assignments"
    )
    
    # Indexes for common queries
    __table_args__ = (
        # Find active assignments for a study
        Index('ix_study_team_active', 'study_id', 'is_active'),
        # Find active assignments for a user
        Index('ix_user_team_active', 'user_id', 'is_active'),
        # Find assignments in date range
        Index('ix_team_dates', 'effective_start_date', 'effective_end_date'),
    )
    
    def __repr__(self) -> str:
        status = "active" if self.is_active else f"ended:{self.departure_reason}"
        return (
            f"<StudyTeamAssignment(user_id={self.user_id}, study_id={self.study_id}, "
            f"job={self.job_type}, alloc={self.allocation_percentage}%, status={status})>"
        )
    
    @property
    def experience_multiplier(self) -> float:
        """Get the experience multiplier for estimation calculations."""
        try:
            return EXPERIENCE_MULTIPLIERS[ExperienceLevel(self.experience_level)]
        except (ValueError, KeyError):
            return 1.0  # Default to MID if invalid
    
    @property
    def effective_weekly_hours(self) -> float:
        """Calculate effective productive hours per week.
        
        Formula: 40 hours * allocation% * productive_time_factor%
        Example: 40 * 0.50 * 0.75 = 15 hours/week
        """
        return 40 * (self.allocation_percentage / 100) * (self.productive_time_factor / 100)
    
    @property
    def is_current(self) -> bool:
        """Check if this assignment is currently active (no end date)."""
        return self.is_active and self.effective_end_date is None

