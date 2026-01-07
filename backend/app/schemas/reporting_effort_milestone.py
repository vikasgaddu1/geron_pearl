"""Pydantic schemas for ReportingEffortMilestone."""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict, field_validator


# Valid subtypes for linking
VALID_LINKED_SUBTYPES = ['Table', 'Listing', 'Figure', 'SDTM', 'ADaM']


class ReportingEffortMilestoneBase(BaseModel):
    """Base schema for ReportingEffortMilestone."""

    name: str = Field(..., min_length=1, max_length=500, description="Milestone name/description")
    start_date: Optional[date] = Field(None, description="Start date for the milestone")
    due_date: Optional[date] = Field(None, description="Target due date")
    responsibility: Optional[str] = Field(None, max_length=255, description="Responsible party")
    comments: Optional[str] = Field(None, description="Additional notes or comments")
    is_completed: bool = Field(False, description="Whether the milestone is completed")
    completion_date: Optional[date] = Field(None, description="Actual completion date")
    display_order: int = Field(0, ge=0, description="Display order within the phase")
    linked_subtype: Optional[str] = Field(None, description="Item subtype to auto-link (Table, Listing, Figure, SDTM, ADaM)")
    linked_tag_id: Optional[int] = Field(None, description="Tag ID to auto-link trackers with this tag")

    @field_validator('linked_subtype')
    @classmethod
    def validate_linked_subtype(cls, v):
        if v is not None and v not in VALID_LINKED_SUBTYPES:
            raise ValueError(f"linked_subtype must be one of: {VALID_LINKED_SUBTYPES}")
        return v


class ReportingEffortMilestoneCreate(ReportingEffortMilestoneBase):
    """Schema for creating a ReportingEffortMilestone."""
    
    phase_id: int = Field(..., gt=0, description="ID of the parent phase")


class ReportingEffortMilestoneUpdate(BaseModel):
    """Schema for updating a ReportingEffortMilestone."""

    name: Optional[str] = Field(None, min_length=1, max_length=500, description="Milestone name/description")
    start_date: Optional[date] = Field(None, description="Start date for the milestone")
    due_date: Optional[date] = Field(None, description="Target due date")
    responsibility: Optional[str] = Field(None, max_length=255, description="Responsible party")
    comments: Optional[str] = Field(None, description="Additional notes or comments")
    is_completed: Optional[bool] = Field(None, description="Whether the milestone is completed")
    completion_date: Optional[date] = Field(None, description="Actual completion date")
    display_order: Optional[int] = Field(None, ge=0, description="Display order within the phase")
    linked_subtype: Optional[str] = Field(None, description="Item subtype to auto-link")
    linked_tag_id: Optional[int] = Field(None, description="Tag ID to auto-link")

    @field_validator('linked_subtype')
    @classmethod
    def validate_linked_subtype(cls, v):
        if v is not None and v not in VALID_LINKED_SUBTYPES:
            raise ValueError(f"linked_subtype must be one of: {VALID_LINKED_SUBTYPES}")
        return v


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


class ReportingEffortMilestoneWithTrackers(ReportingEffortMilestoneInDB):
    """Schema for ReportingEffortMilestone with linked tracker information."""

    linked_tag_name: Optional[str] = Field(None, description="Name of the linked tag (if any)")
    linked_tracker_ids: List[int] = Field(default_factory=list, description="IDs of manually linked trackers")
    linked_tracker_count: int = Field(0, description="Total count of linked trackers (all link types)")
    trackers_past_due: int = Field(0, description="Count of linked trackers with due_date > milestone due_date")

    model_config = ConfigDict(from_attributes=True)





