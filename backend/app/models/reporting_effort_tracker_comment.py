"""SQLAlchemy model for ReportingEffortTrackerComment."""

from enum import Enum
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional, List
from datetime import datetime

from app.db.base import Base


class CommentType(str, Enum):
    """Comment type enum."""
    PROGRAMMER_COMMENT = "programmer_comment"
    BIOSTAT_COMMENT = "biostat_comment"
    SYSTEM_NOTE = "system_note"

if TYPE_CHECKING:
    from app.models.reporting_effort_item_tracker import ReportingEffortItemTracker
    from app.models.user import User


class ReportingEffortTrackerComment(Base):
    """Comments for reporting effort tracker items."""
    
    __tablename__ = "reporting_effort_tracker_comments"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    tracker_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("reporting_effort_item_tracker.id"),
        nullable=False,
        index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    parent_comment_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("reporting_effort_tracker_comments.id"),
        nullable=True
    )
    
    # Comment content
    comment_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="The actual comment text"
    )
    comment_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        doc="Type: programmer_comment, biostat_comment, system_note"
    )
    comment_category: Mapped[str] = mapped_column(
        String(50),
        default="general",
        nullable=False,
        doc="Category: general, production, qc, issue, resolution"
    )
    
    # Comment metadata
    is_pinned: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether this comment is pinned"
    )
    is_edited: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether this comment has been edited"
    )
    edited_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        doc="When the comment was last edited"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="When the comment was created"
    )
    
    # Relationships
    tracker: Mapped["ReportingEffortItemTracker"] = relationship(
        "ReportingEffortItemTracker",
        back_populates="comments"
    )
    user: Mapped["User"] = relationship(
        "User",
        backref="tracker_comments"
    )
    parent_comment: Mapped[Optional["ReportingEffortTrackerComment"]] = relationship(
        "ReportingEffortTrackerComment",
        remote_side=[id],
        backref="replies"
    )
    
    def __repr__(self) -> str:
        return f"<ReportingEffortTrackerComment(id={self.id}, tracker={self.tracker_id}, user={self.user_id}, type={self.comment_type})>"