"""SQLAlchemy model for ReportingEffortDatasetDetails."""

from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.reporting_effort_item import ReportingEffortItem


class ReportingEffortDatasetDetails(Base):
    """Dataset-specific details for reporting effort items."""
    
    __tablename__ = "reporting_effort_dataset_details"
    
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
    
    # Dataset details
    label: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Dataset label or description"
    )
    sorting_order: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Display/sorting order for the dataset"
    )
    acronyms: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON array of acronyms specific to this dataset"
    )
    
    # Relationships
    reporting_effort_item: Mapped["ReportingEffortItem"] = relationship(
        "ReportingEffortItem",
        back_populates="dataset_details"
    )
    
    def __repr__(self) -> str:
        return f"<ReportingEffortDatasetDetails(id={self.id}, item_id={self.reporting_effort_item_id}, label='{self.label}')>"