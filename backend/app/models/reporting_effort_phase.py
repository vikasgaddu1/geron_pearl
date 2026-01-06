"""SQLAlchemy model for ReportingEffortPhase."""

from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, List

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.reporting_effort import ReportingEffort
    from app.models.reporting_effort_milestone import ReportingEffortMilestone


class ReportingEffortPhase(Base, TimestampMixin):
    """Phase model representing a group of milestones within a reporting effort.
    
    Examples: 'Blinded DMC/DSMT (Feb2026) Delivery', 'Unblinded HEC Delivery'
    """
    
    __tablename__ = "reporting_effort_phases"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    reporting_effort_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("reporting_efforts.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    # Data fields
    name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        doc="Phase name (e.g., 'Blinded DMC/DSMT Delivery')"
    )
    display_order: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=0,
        doc="Order in which phases are displayed"
    )
    
    # Relationships
    reporting_effort: Mapped["ReportingEffort"] = relationship(
        "ReportingEffort", 
        back_populates="phases"
    )
    milestones: Mapped[List["ReportingEffortMilestone"]] = relationship(
        "ReportingEffortMilestone",
        back_populates="phase",
        cascade="all, delete-orphan",
        order_by="ReportingEffortMilestone.display_order"
    )
    
    def __repr__(self) -> str:
        return f"<ReportingEffortPhase(id={self.id}, name='{self.name}')>"

