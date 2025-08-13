"""Pydantic schemas for ReportingEffortTrackerComment."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.models.reporting_effort_tracker_comment import CommentType


class ReportingEffortTrackerCommentBase(BaseModel):
    """Base schema for ReportingEffortTrackerComment."""
    
    comment_text: str = Field(..., min_length=1, description="Comment content")
    comment_type: CommentType = Field(..., description="Type of comment: biostat_comment or programmer_comment")


class ReportingEffortTrackerCommentCreate(ReportingEffortTrackerCommentBase):
    """Schema for creating a ReportingEffortTrackerComment."""
    
    reporting_effort_item_id: int = Field(..., description="ID of the reporting effort item")
    parent_comment_id: Optional[int] = Field(None, description="ID of parent comment for threading")


class ReportingEffortTrackerCommentUpdate(BaseModel):
    """Schema for updating a ReportingEffortTrackerComment."""
    
    comment_text: Optional[str] = Field(None, min_length=1)
    is_edited: Optional[bool] = None


class ReportingEffortTrackerCommentInDB(ReportingEffortTrackerCommentBase):
    """Schema for ReportingEffortTrackerComment from database."""
    
    id: int
    reporting_effort_item_id: int
    user_id: int
    parent_comment_id: Optional[int] = None
    is_edited: bool
    is_deleted: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ReportingEffortTrackerCommentWithDetails(ReportingEffortTrackerCommentInDB):
    """Schema for ReportingEffortTrackerComment with user and thread details."""
    
    user_name: str
    user_department: Optional[str] = None
    replies: List['ReportingEffortTrackerCommentWithDetails'] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


# Update forward references for recursive model
ReportingEffortTrackerCommentWithDetails.model_rebuild()