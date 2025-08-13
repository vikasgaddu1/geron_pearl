"""SQLAlchemy model for ReportingEffortItemFootnote junction table."""

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.reporting_effort_item import ReportingEffortItem
    from app.models.text_element import TextElement


class ReportingEffortItemFootnote(Base):
    """Junction table for reporting effort items and footnotes."""
    
    __tablename__ = "reporting_effort_item_footnotes"
    
    # Composite primary key
    reporting_effort_item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("reporting_effort_items.id"),
        primary_key=True
    )
    footnote_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("text_elements.id"),
        primary_key=True
    )
    
    # Additional fields
    sequence_number: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Display order for footnotes"
    )
    
    # Relationships
    reporting_effort_item: Mapped["ReportingEffortItem"] = relationship(
        "ReportingEffortItem",
        back_populates="footnotes"
    )
    footnote: Mapped["TextElement"] = relationship("TextElement")
    
    def __repr__(self) -> str:
        return f"<ReportingEffortItemFootnote(item_id={self.reporting_effort_item_id}, footnote_id={self.footnote_id})>"