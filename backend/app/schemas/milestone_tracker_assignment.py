"""Pydantic schemas for MilestoneTrackerAssignment."""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict


class MilestoneTrackerAssignmentBase(BaseModel):
    """Base schema for MilestoneTrackerAssignment."""

    milestone_id: int = Field(..., gt=0, description="ID of the milestone")
    tracker_id: int = Field(..., gt=0, description="ID of the tracker item")


class MilestoneTrackerAssignmentCreate(MilestoneTrackerAssignmentBase):
    """Schema for creating a MilestoneTrackerAssignment."""
    pass


class MilestoneTrackerAssignmentInDB(MilestoneTrackerAssignmentBase):
    """Schema for MilestoneTrackerAssignment from database."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MilestoneTrackerAssignment(MilestoneTrackerAssignmentInDB):
    """Schema for MilestoneTrackerAssignment response."""
    pass


class TrackerMilestoneInfo(BaseModel):
    """Milestone info for displaying on tracker items."""

    milestone_id: int
    milestone_name: str
    milestone_due_date: Optional[date] = None
    is_past_due: bool = Field(False, description="True if tracker.due_date > milestone.due_date")
    link_type: str = Field(..., description="'subtype', 'tag', or 'manual'")

    model_config = ConfigDict(from_attributes=True)


class BulkMilestoneTrackerAssignment(BaseModel):
    """Schema for bulk assigning trackers to a milestone."""

    milestone_id: int = Field(..., gt=0, description="ID of the milestone")
    tracker_ids: List[int] = Field(..., min_length=1, description="List of tracker IDs to assign")


class BulkOperationResult(BaseModel):
    """Result of a bulk operation."""

    success: bool = True
    affected_count: int = 0
    errors: List[str] = Field(default_factory=list)
