"""
Pydantic schemas for simplified tracker comment system
"""

from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


# Valid comment types
CommentTypeEnum = Literal["programming", "biostat"]


class TrackerCommentBase(BaseModel):
    """Base schema for tracker comments"""
    comment_text: str = Field(..., min_length=1, description="Comment content")
    comment_type: CommentTypeEnum = Field(default="programming", description="Comment type: programming or biostat")
    parent_comment_id: Optional[int] = Field(None, description="Parent comment ID for replies")


class TrackerCommentCreate(TrackerCommentBase):
    """Schema for creating a new comment"""
    tracker_id: int = Field(..., description="Tracker ID this comment belongs to")


class TrackerCommentUpdate(BaseModel):
    """Schema for updating comment resolution status"""
    is_resolved: bool = Field(..., description="Resolution status")


class TrackerCommentInDB(TrackerCommentBase):
    """Database representation of comment"""
    id: int
    tracker_id: int
    user_id: int
    comment_type: str = Field(default="programming", description="Comment type: programming or biostat")
    is_resolved: bool
    resolved_by_user_id: Optional[int] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TrackerComment(TrackerCommentInDB):
    """Complete comment schema with user information"""
    username: str = Field(..., description="Username of comment author")
    resolved_by_username: Optional[str] = Field(None, description="Username who resolved the comment")
    is_parent_comment: bool = Field(..., description="True if this is a parent comment, False if reply")
    reply_count: int = Field(0, description="Number of direct replies to this comment")


class TrackerCommentThread(TrackerComment):
    """Comment with nested replies for blog-style display"""
    replies: List["TrackerCommentThread"] = Field(default_factory=list, description="Nested replies")


class TrackerCommentSummary(BaseModel):
    """Summary of comments for a tracker"""
    tracker_id: int
    total_comments: int
    unresolved_count: int  # Only parent comments count toward unresolved badge (total)
    programming_unresolved_count: int = Field(default=0, description="Unresolved programming comments")
    biostat_unresolved_count: int = Field(default=0, description="Unresolved biostat comments")
    resolved_parent_comments: int
    total_replies: int
    latest_comment_at: Optional[datetime] = None


class CommentWithUserInfo(BaseModel):
    """Comment data enriched with user information for API responses"""
    id: int
    tracker_id: int
    user_id: int
    username: str
    parent_comment_id: Optional[int] = None
    comment_text: str
    comment_type: str = Field(default="programming", description="Comment type: programming or biostat")
    is_resolved: bool
    resolved_by_user_id: Optional[int] = None
    resolved_by_username: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_parent_comment: bool

    class Config:
        from_attributes = True


# Update forward references for recursive types
TrackerCommentThread.model_rebuild()