"""
Tracker Comment Model
Simplified comment system for reporting effort tracker items.
"""

from enum import Enum
from typing import Optional
from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class CommentType(str, Enum):
    """Comment type enumeration"""
    qc_comment = "qc_comment"
    prod_comment = "prod_comment"
    biostat_comment = "biostat_comment"


class TrackerComment(Base):
    """
    Tracker Comment Model
    
    Stores comments for reporting effort tracker items with threading support
    and status tracking.
    """
    __tablename__ = "tracker_comments"

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    tracker_id = Column(
        Integer, 
        ForeignKey("reporting_effort_item_tracker.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    user_id = Column(
        Integer, 
        ForeignKey("users.id"), 
        nullable=False, 
        index=True
    )
    parent_comment_id = Column(
        Integer, 
        ForeignKey("tracker_comments.id", ondelete="CASCADE"), 
        nullable=True,
        index=True
    )
    
    # Comment content
    comment_text = Column(Text, nullable=False)
    comment_type = Column(
        SQLEnum(CommentType), 
        nullable=False, 
        default=CommentType.qc_comment,
        index=True
    )
    
    # Status fields
    is_resolved = Column(Boolean, default=False, nullable=False)
    is_pinned = Column(Boolean, default=False, nullable=False)
    is_tracked = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # Resolution tracking
    resolved_by_user_id = Column(
        Integer, 
        ForeignKey("users.id"), 
        nullable=True
    )
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    tracker = relationship(
        "ReportingEffortItemTracker", 
        back_populates="comments"
    )
    user = relationship(
        "User", 
        foreign_keys=[user_id],
        back_populates="comments"
    )
    resolved_by_user = relationship(
        "User", 
        foreign_keys=[resolved_by_user_id],
        back_populates="resolved_comments"
    )
    
    # Self-referential relationship for threading
    parent_comment = relationship(
        "TrackerComment", 
        remote_side=[id],
        back_populates="replies"
    )
    replies = relationship(
        "TrackerComment", 
        back_populates="parent_comment",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        try:
            return f"<TrackerComment(id={self.id}, tracker_id={self.tracker_id}, type={self.comment_type})>"
        except Exception:
            return f"<TrackerComment(detached)>"