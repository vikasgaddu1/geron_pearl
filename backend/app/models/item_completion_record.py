"""ItemCompletionRecord model for tracking item completions and velocity calculation.

This model records completion events to enable:
- Throughput-based velocity calculations
- Historical analysis of completion patterns
- Self-improving estimation based on actual data
"""

from datetime import datetime
from sqlalchemy import Integer, String, ForeignKey, DateTime, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional

from app.db.base import Base
from app.db.mixins import TimestampMixin


if TYPE_CHECKING:
    from app.models.reporting_effort_item_tracker import ReportingEffortItemTracker
    from app.models.study import Study
    from app.models.user import User


class ItemCompletionRecord(Base, TimestampMixin):
    """Records completion events for velocity calculation.
    
    This table is automatically populated when a tracker item's
    production_status changes to 'completed'.
    
    It captures a snapshot of the item and programmer details at completion time,
    which is essential for accurate velocity calculations even when:
    - Team members leave (their history is preserved)
    - Items are reassigned (original completion context maintained)
    - Allocation percentages change over time
    
    Velocity is calculated as: complexity_points / time_period
    Example: A programmer completing 15 complexity points in a week = 15 points/week velocity
    """
    
    __tablename__ = "item_completion_records"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Reference to the original tracker (may be null if tracker deleted)
    tracker_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("reporting_effort_item_tracker.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Study context (denormalized for faster queries)
    study_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("studies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Item details at completion time (snapshot)
    item_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Item type: TLF or Dataset"
    )
    item_subtype: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Subtype: Table, Listing, Figure, SDTM, ADaM"
    )
    item_code: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="The TLF ID or dataset name"
    )
    complexity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Complexity score at completion (1-5)"
    )
    
    # Programmer details at completion time (snapshot)
    production_programmer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    programmer_experience_level: Mapped[str] = mapped_column(
        String(20),
        nullable=True,
        doc="Experience level at completion: JUNIOR, MID, SENIOR"
    )
    programmer_allocation_percent: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        doc="Programmer's allocation percentage to this study at completion"
    )
    
    # Completion timing
    completed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
        doc="Timestamp when production_status became 'completed'"
    )
    iso_week: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        doc="ISO week number for weekly aggregation (1-53)"
    )
    iso_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        doc="ISO year for aggregation"
    )
    
    # Sister study context (for analyzing code reuse impact)
    had_sister_study: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether a sister study existed at completion time"
    )
    sister_study_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("studies.id", ondelete="SET NULL"),
        nullable=True,
        doc="ID of sister study if code was reused"
    )
    
    # Relationships
    tracker: Mapped[Optional["ReportingEffortItemTracker"]] = relationship(
        "ReportingEffortItemTracker",
        foreign_keys=[tracker_id],
        backref="completion_records"
    )
    study: Mapped["Study"] = relationship(
        "Study",
        foreign_keys=[study_id],
        backref="completion_records"
    )
    production_programmer: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[production_programmer_id],
        backref="completed_items"
    )
    sister_study: Mapped[Optional["Study"]] = relationship(
        "Study",
        foreign_keys=[sister_study_id]
    )
    
    # Indexes for common queries
    __table_args__ = (
        # Weekly velocity queries
        Index('ix_completion_week', 'iso_year', 'iso_week'),
        # Programmer velocity queries
        Index('ix_completion_programmer_week', 'production_programmer_id', 'iso_year', 'iso_week'),
        # Study velocity queries  
        Index('ix_completion_study_week', 'study_id', 'iso_year', 'iso_week'),
        # Item type analysis
        Index('ix_completion_item_type', 'item_subtype', 'complexity'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<ItemCompletionRecord(id={self.id}, tracker={self.tracker_id}, "
            f"study={self.study_id}, programmer={self.production_programmer_id}, "
            f"complexity={self.complexity}, week={self.iso_year}-W{self.iso_week})>"
        )

