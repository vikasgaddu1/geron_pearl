"""SQLAlchemy model for ReportingEffortItem."""

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, UniqueConstraint, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional, List

from app.db.base import Base
from app.db.mixins import TimestampMixin
from app.models.enums import ItemType, SourceType

if TYPE_CHECKING:
    from app.models.reporting_effort import ReportingEffort
    from app.models.reporting_effort_item_tracker import ReportingEffortItemTracker
    from app.models.reporting_effort_tlf_details import ReportingEffortTlfDetails
    from app.models.reporting_effort_dataset_details import ReportingEffortDatasetDetails
    from app.models.reporting_effort_item_footnote import ReportingEffortItemFootnote
    from app.models.reporting_effort_item_acronym import ReportingEffortItemAcronym


class ReportingEffortItem(Base, TimestampMixin):
    """ReportingEffortItem model for TLFs and Datasets in reporting efforts."""
    
    __tablename__ = "reporting_effort_items"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    reporting_effort_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("reporting_efforts.id"), 
        nullable=False, 
        index=True
    )
    
    # Source tracking
    # Database enum 'sourcetype' stores enum VALUES (lowercase): 'package', 'reporting_effort', 'custom', 'bulk_upload'
    # SQLAlchemy enum is configured to use enum values, not names
    source_type: Mapped[Optional[SourceType]] = mapped_column(
        Enum(
            SourceType,
            name='sourcetype',
            create_type=False,
            native_enum=False
        ),
        nullable=True,
        doc="Where this item came from"
    )
    source_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="ID of source package or reporting effort"
    )
    source_item_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="ID of specific item if copied from another item"
    )
    
    # Item details
    item_type: Mapped[ItemType] = mapped_column(
        Enum(
            ItemType,
            name='itemtype',
            create_type=False,
            native_enum=False
        ),
        nullable=False,
        index=True,
        doc="Type of item (TLF or Dataset)"
    )
    item_subtype: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Subtype: Table/Listing/Figure for TLF, SDTM/ADaM for Dataset"
    )
    item_code: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="The actual TLF ID or dataset name"
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Soft delete flag"
    )
    
    # Relationships
    reporting_effort: Mapped["ReportingEffort"] = relationship(
        "ReportingEffort", 
        back_populates="items"
    )
    tracker: Mapped[Optional["ReportingEffortItemTracker"]] = relationship(
        "ReportingEffortItemTracker",
        back_populates="item",
        uselist=False,
        cascade="all, delete-orphan"
    )
    tlf_details: Mapped[Optional["ReportingEffortTlfDetails"]] = relationship(
        "ReportingEffortTlfDetails",
        back_populates="reporting_effort_item",
        uselist=False,
        cascade="all, delete-orphan"
    )
    dataset_details: Mapped[Optional["ReportingEffortDatasetDetails"]] = relationship(
        "ReportingEffortDatasetDetails",
        back_populates="reporting_effort_item",
        uselist=False,
        cascade="all, delete-orphan"
    )
    footnotes: Mapped[List["ReportingEffortItemFootnote"]] = relationship(
        "ReportingEffortItemFootnote",
        back_populates="reporting_effort_item",
        cascade="all, delete-orphan"
    )
    acronyms: Mapped[List["ReportingEffortItemAcronym"]] = relationship(
        "ReportingEffortItemAcronym",
        back_populates="reporting_effort_item",
        cascade="all, delete-orphan"
    )
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint(
            'reporting_effort_id', 'item_type', 'item_subtype', 'item_code',
            name='uq_reporting_effort_item_unique'
        ),
        {"sqlite_autoincrement": True},
    )
    
    def __repr__(self) -> str:
        return f"<ReportingEffortItem(id={self.id}, effort={self.reporting_effort_id}, type={self.item_type.value}, code='{self.item_code}')>"