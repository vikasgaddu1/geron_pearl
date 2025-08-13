"""SQLAlchemy model for ReportingEffortItemTracker."""

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional, List
from datetime import date

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.reporting_effort_item import ReportingEffortItem
    from app.models.user import User
    from app.models.reporting_effort_tracker_comment import ReportingEffortTrackerComment


class ReportingEffortItemTracker(Base, TimestampMixin):
    """Tracker for reporting effort items - manages workflow and assignments."""
    
    __tablename__ = "reporting_effort_item_tracker"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    reporting_effort_item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("reporting_effort_items.id"),
        nullable=False,
        unique=True,
        index=True
    )
    production_programmer_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )
    qc_programmer_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )
    
    # Status fields
    production_status: Mapped[str] = mapped_column(
        String(50),
        default="not_started",
        nullable=False,
        doc="Status: not_started, in_progress, completed, on_hold"
    )
    qc_status: Mapped[str] = mapped_column(
        String(50),
        default="not_started",
        nullable=False,
        doc="QC Status: not_started, in_progress, completed, failed"
    )
    
    # Scheduling fields
    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        doc="Due date for completion"
    )
    qc_completion_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        doc="Date when QC was completed"
    )
    
    # Priority and workflow
    priority: Mapped[str] = mapped_column(
        String(50),
        default="medium",
        nullable=False,
        doc="Priority: low, medium, high, critical"
    )
    qc_level: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="QC Level: level1, level2, level3"
    )
    in_production_flag: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether item is currently in production"
    )
    
    # Relationships
    item: Mapped["ReportingEffortItem"] = relationship(
        "ReportingEffortItem",
        back_populates="tracker"
    )
    production_programmer: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[production_programmer_id],
        backref="production_assignments"
    )
    qc_programmer: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[qc_programmer_id],
        backref="qc_assignments"
    )
    comments: Mapped[List["ReportingEffortTrackerComment"]] = relationship(
        "ReportingEffortTrackerComment",
        back_populates="tracker",
        cascade="all, delete-orphan",
        order_by="ReportingEffortTrackerComment.created_at.desc()"
    )
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('reporting_effort_item_id', name='uq_tracker_item'),
        {"sqlite_autoincrement": True},
    )
    
    def __repr__(self) -> str:
        return f"<ReportingEffortItemTracker(id={self.id}, item={self.reporting_effort_item_id}, prod_status={self.production_status}, qc_status={self.qc_status})>"