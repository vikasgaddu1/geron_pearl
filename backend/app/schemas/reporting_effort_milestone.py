"""Pydantic schemas for ReportingEffortMilestone."""

from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict


class ReportingEffortMilestoneBase(BaseModel):
    """Base schema for ReportingEffortMilestone."""
    
    name: str = Field(..., min_length=1, max_length=500, description="Milestone name/description")
    due_date: Optional[date] = Field(None, description="Target due date")
    responsibility: Optional[str] = Field(None, max_length=255, description="Responsible party")
    comments: Optional[str] = Field(None, description="Additional notes or comments")
    is_completed: bool = Field(False, description="Whether the milestone is completed")
    completion_date: Optional[date] = Field(None, description="Actual completion date")
    display_order: int = Field(0, ge=0, description="Display order within the phase")


class ReportingEffortMilestoneCreate(ReportingEffortMilestoneBase):
    """Schema for creating a ReportingEffortMilestone."""
    
    phase_id: int = Field(..., gt=0, description="ID of the parent phase")


class ReportingEffortMilestoneUpdate(BaseModel):
    """Schema for updating a ReportingEffortMilestone."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=500, description="Milestone name/description")
    due_date: Optional[date] = Field(None, description="Target due date")
    responsibility: Optional[str] = Field(None, max_length=255, description="Responsible party")
    comments: Optional[str] = Field(None, description="Additional notes or comments")
    is_completed: Optional[bool] = Field(None, description="Whether the milestone is completed")
    completion_date: Optional[date] = Field(None, description="Actual completion date")
    display_order: Optional[int] = Field(None, ge=0, description="Display order within the phase")


class ReportingEffortMilestoneInDB(ReportingEffortMilestoneBase):
    """Schema for ReportingEffortMilestone from database."""
    
    id: int
    phase_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ReportingEffortMilestone(ReportingEffortMilestoneInDB):
    """Schema for ReportingEffortMilestone response."""
    pass


class ReportingEffortMilestoneWithPhase(ReportingEffortMilestoneInDB):
    """Schema for ReportingEffortMilestone with phase info for dashboard display."""
    
    phase_name: Optional[str] = None
    reporting_effort_id: Optional[int] = None
    reporting_effort_label: Optional[str] = None
    study_id: Optional[int] = None
    study_label: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

