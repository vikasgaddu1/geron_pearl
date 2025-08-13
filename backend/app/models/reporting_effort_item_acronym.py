"""SQLAlchemy model for ReportingEffortItemAcronym junction table."""

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.reporting_effort_item import ReportingEffortItem
    from app.models.text_element import TextElement


class ReportingEffortItemAcronym(Base):
    """Junction table for reporting effort items and acronyms."""
    
    __tablename__ = "reporting_effort_item_acronyms"
    
    # Composite primary key
    reporting_effort_item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("reporting_effort_items.id"),
        primary_key=True
    )
    acronym_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("text_elements.id"),
        primary_key=True
    )
    
    # Relationships
    reporting_effort_item: Mapped["ReportingEffortItem"] = relationship(
        "ReportingEffortItem",
        back_populates="acronyms"
    )
    acronym: Mapped["TextElement"] = relationship("TextElement")
    
    def __repr__(self) -> str:
        return f"<ReportingEffortItemAcronym(item_id={self.reporting_effort_item_id}, acronym_id={self.acronym_id})>"