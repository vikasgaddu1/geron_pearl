"""SQLAlchemy models for Tracker Tags.

Provides a flexible tagging system for categorizing tracker items
(e.g., "Topline Deliverable", "Batch 1", "Batch 2", "Batch 3").
Each tag has a customizable color for visual identification.
"""

from typing import TYPE_CHECKING, List
from sqlalchemy import Column, Integer, String, Text, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.reporting_effort_item_tracker import ReportingEffortItemTracker


class TrackerTag(Base, TimestampMixin):
    """
    Tag definition model.
    
    Reusable tags that can be assigned to any tracker item.
    Each tag has a name, color, and optional description.
    """
    __tablename__ = "tracker_tags"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Tag details
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        doc="Tag name (e.g., 'Topline', 'Batch 1')"
    )
    color: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        default="#3B82F6",
        doc="Hex color code (e.g., '#FF5733')"
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        doc="Optional description of the tag's purpose"
    )
    
    # Relationships
    tracker_associations: Mapped[List["TrackerItemTag"]] = relationship(
        "TrackerItemTag",
        back_populates="tag",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<TrackerTag(id={self.id}, name='{self.name}', color='{self.color}')>"


class TrackerItemTag(Base):
    """
    Many-to-many association between trackers and tags.
    
    Links tracker items to their assigned tags.
    """
    __tablename__ = "tracker_item_tags"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    tracker_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("reporting_effort_item_tracker.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Reference to the tracker item"
    )
    tag_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tracker_tags.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Reference to the tag"
    )
    
    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    tracker: Mapped["ReportingEffortItemTracker"] = relationship(
        "ReportingEffortItemTracker",
        back_populates="tag_associations"
    )
    tag: Mapped["TrackerTag"] = relationship(
        "TrackerTag",
        back_populates="tracker_associations"
    )
    
    # Unique constraint to prevent duplicate tag assignments
    __table_args__ = (
        UniqueConstraint('tracker_id', 'tag_id', name='uq_tracker_tag'),
        {"sqlite_autoincrement": True},
    )
    
    def __repr__(self) -> str:
        return f"<TrackerItemTag(tracker_id={self.tracker_id}, tag_id={self.tag_id})>"

