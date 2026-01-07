"""SQLAlchemy models for ReportingEffort Use Cases."""

from typing import TYPE_CHECKING, List
from sqlalchemy import Integer, String, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.reporting_effort import ReportingEffort


class ReportingEffortUseCase(Base, TimestampMixin):
    """
    Defines available use cases that can be assigned to reporting efforts.
    Examples: Clinical, Non-Clinical, Publication, Labeling, CMC, Regulatory, etc.
    """

    __tablename__ = "reporting_effort_usecases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#3B82F6")
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationship to associations
    assignments: Mapped[List["ReportingEffortUseCaseAssignment"]] = relationship(
        "ReportingEffortUseCaseAssignment",
        back_populates="use_case",
        cascade="all, delete-orphan"
    )


class ReportingEffortUseCaseAssignment(Base):
    """
    Many-to-many association between ReportingEfforts and UseCases.
    """

    __tablename__ = "reporting_effort_usecase_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    reporting_effort_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("reporting_efforts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    use_case_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("reporting_effort_usecases.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_at: Mapped[str] = mapped_column(server_default=func.now())

    # Relationships
    reporting_effort: Mapped["ReportingEffort"] = relationship(
        "ReportingEffort",
        back_populates="use_case_assignments"
    )
    use_case: Mapped["ReportingEffortUseCase"] = relationship(
        "ReportingEffortUseCase",
        back_populates="assignments"
    )

    __table_args__ = (
        UniqueConstraint('reporting_effort_id', 'use_case_id', name='uq_effort_usecase'),
    )
