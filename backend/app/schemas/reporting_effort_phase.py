"""Pydantic schemas for ReportingEffortPhase."""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict


class ReportingEffortPhaseBase(BaseModel):
    """Base schema for ReportingEffortPhase."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Phase name")
    display_order: int = Field(0, ge=0, description="Display order of the phase")


class ReportingEffortPhaseCreate(ReportingEffortPhaseBase):
    """Schema for creating a ReportingEffortPhase."""
    
    reporting_effort_id: int = Field(..., gt=0, description="ID of the reporting effort")


class ReportingEffortPhaseUpdate(BaseModel):
    """Schema for updating a ReportingEffortPhase."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Phase name")
    display_order: Optional[int] = Field(None, ge=0, description="Display order of the phase")


class ReportingEffortPhaseInDB(ReportingEffortPhaseBase):
    """Schema for ReportingEffortPhase from database."""
    
    id: int
    reporting_effort_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ReportingEffortPhase(ReportingEffortPhaseInDB):
    """Schema for ReportingEffortPhase response."""
    pass


# Forward reference for milestone - will be resolved after import
class ReportingEffortMilestoneInPhase(BaseModel):
    """Milestone schema for nesting within Phase response."""

    id: int
    phase_id: int
    name: str
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    responsibility: Optional[str] = None
    comments: Optional[str] = None
    is_completed: bool = False
    completion_date: Optional[date] = None
    display_order: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportingEffortPhaseWithMilestones(ReportingEffortPhaseInDB):
    """Schema for ReportingEffortPhase with nested milestones."""
    
    milestones: List[ReportingEffortMilestoneInPhase] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)






