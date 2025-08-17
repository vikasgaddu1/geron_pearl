"""
Pydantic schemas for TrackerComment model
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.tracker_comment import CommentType


# Base schema with common fields
class TrackerCommentBase(BaseModel):
    """Base schema for tracker comments"""
    comment_text: str = Field(..., min_length=1, max_length=5000)
    comment_type: CommentType = Field(default=CommentType.qc_comment)
    is_tracked: bool = Field(default=False)
    is_pinned: bool = Field(default=False)


# Schema for creating comments
class TrackerCommentCreate(TrackerCommentBase):
    """Schema for creating new comments"""
    tracker_id: int = Field(..., gt=0)
    parent_comment_id: Optional[int] = Field(default=None, gt=0)


# Schema for updating comments
class TrackerCommentUpdate(BaseModel):
    """Schema for updating existing comments"""
    comment_text: Optional[str] = Field(None, min_length=1, max_length=5000)
    comment_type: Optional[CommentType] = None
    is_tracked: Optional[bool] = None
    is_pinned: Optional[bool] = None
    is_resolved: Optional[bool] = None


# User schema for embedding in comment responses
class CommentUser(BaseModel):
    """User information for comment responses"""
    id: int
    username: str
    role: Optional[str] = None

    class Config:
        from_attributes = True


# Schema for database responses
class TrackerCommentInDB(TrackerCommentBase):
    """Database representation of comment"""
    id: int
    tracker_id: int
    user_id: int
    parent_comment_id: Optional[int] = None
    is_resolved: bool
    is_deleted: bool
    resolved_by_user_id: Optional[int] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Schema for API responses with user information
class TrackerComment(TrackerCommentInDB):
    """Full comment schema with user information"""
    user: CommentUser
    resolved_by_user: Optional[CommentUser] = None
    replies: List["TrackerComment"] = []

    class Config:
        from_attributes = True


# Schema for comment summaries
class CommentSummary(BaseModel):
    """Summary of comments for a tracker item"""
    tracker_id: int
    total_comments: int
    unresolved_comments: int
    pinned_comments: int
    last_comment_at: Optional[datetime] = None
    last_comment_type: Optional[CommentType] = None
    last_comment_user: Optional[str] = None


# Schema for batch operations
class TrackerCommentBatch(BaseModel):
    """Schema for batch comment operations"""
    tracker_ids: List[int] = Field(..., min_items=1)
    action: str = Field(..., pattern="^(mark_resolved|mark_unresolved|delete)$")
    comment_ids: Optional[List[int]] = None


# Schema for comment search/filter
class CommentFilter(BaseModel):
    """Schema for filtering comments"""
    tracker_ids: Optional[List[int]] = None
    comment_types: Optional[List[CommentType]] = None
    is_resolved: Optional[bool] = None
    is_pinned: Optional[bool] = None
    user_ids: Optional[List[int]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search_text: Optional[str] = None


# Schema for resolving comments
class CommentResolve(BaseModel):
    """Schema for resolving/unresolving comments"""
    comment_id: int = Field(..., gt=0)
    is_resolved: bool = True
    resolution_note: Optional[str] = Field(None, max_length=500)


# Update forward reference for recursive relationship
TrackerComment.model_rebuild()