"""SQLAlchemy model for ReportingEffort."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.study import Study
    from app.models.database_release import DatabaseRelease
    from app.models.reporting_effort_item import ReportingEffortItem
    from app.models.reporting_effort_phase import ReportingEffortPhase
    from app.models.reporting_effort_usecase import ReportingEffortUseCaseAssignment
    from app.models.user import User


class ReportingEffort(Base, TimestampMixin):
    """ReportingEffort model representing reporting efforts for database releases."""
    
    __tablename__ = "reporting_efforts"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    study_id: Mapped[int] = mapped_column(Integer, ForeignKey("studies.id"), nullable=False, index=True)
    database_release_id: Mapped[int] = mapped_column(Integer, ForeignKey("database_releases.id"), nullable=False, index=True)
    
    # Data fields
    database_release_label: Mapped[str] = mapped_column(String(255), nullable=False)

    # Lock fields
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    locked_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    lock_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    study: Mapped["Study"] = relationship("Study", back_populates="reporting_efforts")
    database_release: Mapped["DatabaseRelease"] = relationship("DatabaseRelease", back_populates="reporting_efforts")
    items: Mapped[List["ReportingEffortItem"]] = relationship(
        "ReportingEffortItem",
        back_populates="reporting_effort",
        cascade="all, delete-orphan"
    )
    phases: Mapped[List["ReportingEffortPhase"]] = relationship(
        "ReportingEffortPhase",
        back_populates="reporting_effort",
        cascade="all, delete-orphan",
        order_by="ReportingEffortPhase.display_order"
    )
    use_case_assignments: Mapped[List["ReportingEffortUseCaseAssignment"]] = relationship(
        "ReportingEffortUseCaseAssignment",
        back_populates="reporting_effort",
        cascade="all, delete-orphan"
    )
    locked_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[locked_by_id])

    # Unique constraint to prevent duplicate reporting efforts for same database release with same label
    __table_args__ = (
        UniqueConstraint('database_release_id', 'database_release_label', name='uq_database_release_reporting_effort_label'),
        {"sqlite_autoincrement": True},
    )