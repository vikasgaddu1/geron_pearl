"""
Simplified Tracker Comment Model
Blog-style comment system for reporting effort tracker items.
"""

from typing import Optional, List
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class TrackerComment(Base):
    """
    Simplified Tracker Comment Model
    
    Blog-style threading system with username display and simple resolved status.
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
    
    # Simple status tracking
    is_resolved = Column(Boolean, default=False, nullable=False, index=True)
    
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
        nullable=False,
        index=True
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
    
    # Self-referential relationship for blog-style threading
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
            return f"<TrackerComment(id={self.id}, tracker_id={self.tracker_id}, is_resolved={self.is_resolved})>"
        except Exception:
            return f"<TrackerComment(detached)>"
    
    @property
    def is_parent_comment(self) -> bool:
        """Check if this is a parent comment (not a reply)."""
        return self.parent_comment_id is None
    
    def get_all_replies(self) -> List["TrackerComment"]:
        """Get all replies in chronological order (for blog-style display)."""
        def collect_replies(comment):
            replies = []
            for reply in sorted(comment.replies, key=lambda x: x.created_at):
                replies.append(reply)
                replies.extend(collect_replies(reply))  # Recursive for nested replies
            return replies
        
        return collect_replies(self)