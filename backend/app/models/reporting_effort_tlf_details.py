"""SQLAlchemy model for ReportingEffortTlfDetails."""

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.reporting_effort_item import ReportingEffortItem
    from app.models.text_element import TextElement


class ReportingEffortTlfDetails(Base):
    """TLF-specific details for reporting effort items."""
    
    __tablename__ = "reporting_effort_tlf_details"
    
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
    title_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("text_elements.id"),
        nullable=True,
        doc="Reference to title text element"
    )
    population_flag_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("text_elements.id"),
        nullable=True,
        doc="Reference to population flag text element"
    )
    ich_category_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("text_elements.id"),
        nullable=True,
        doc="Reference to ICH category text element"
    )
    
    # Relationships
    reporting_effort_item: Mapped["ReportingEffortItem"] = relationship(
        "ReportingEffortItem",
        back_populates="tlf_details"
    )
    title: Mapped[Optional["TextElement"]] = relationship(
        "TextElement",
        foreign_keys=[title_id]
    )
    population_flag: Mapped[Optional["TextElement"]] = relationship(
        "TextElement",
        foreign_keys=[population_flag_id]
    )
    ich_category: Mapped[Optional["TextElement"]] = relationship(
        "TextElement",
        foreign_keys=[ich_category_id]
    )
    
    def __repr__(self) -> str:
        return f"<ReportingEffortTlfDetails(id={self.id}, item_id={self.reporting_effort_item_id})>"