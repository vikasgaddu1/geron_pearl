"""Pydantic schemas for ReportingEffortItemTracker."""

from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict

from app.models.reporting_effort_item_tracker import ProductionStatus, QCStatus, BiostatStatus



class ReportingEffortItemTrackerBase(BaseModel):
    """Base schema for ReportingEffortItemTracker."""
    
    production_programmer_id: Optional[int] = Field(None, description="User ID of production programmer")
    production_status: Optional[ProductionStatus] = Field(None, description="Production status")
    due_date: Optional[date] = Field(None, description="Target completion date")
    priority: Optional[str] = Field(None, description="Priority level: low, medium, high, critical")
    qc_level: Optional[str] = Field(None, max_length=50, description="QC level required")
    qc_programmer_id: Optional[int] = Field(None, description="User ID of QC programmer")
    qc_status: Optional[QCStatus] = Field(None, description="QC status")
    qc_completion_date: Optional[date] = Field(None, description="QC completion date")
    biostat_reviewer_id: Optional[int] = Field(None, description="User ID of biostat reviewer (TLF items only)")
    biostat_status: Optional[BiostatStatus] = Field(None, description="Biostat review status: not_applicable, pending, passed, failed")
    biostat_review_date: Optional[date] = Field(None, description="Date when biostat review was completed")
    in_production_flag: bool = Field(False, description="Whether item is currently in production")
    complexity: int = Field(
        default=3, 
        ge=1, 
        le=5, 
        description="Complexity score: 1=trivial, 2=simple, 3=standard, 4=complex, 5=very complex"
    )


class ReportingEffortItemTrackerCreate(ReportingEffortItemTrackerBase):
    """Schema for creating a ReportingEffortItemTracker."""
    
    reporting_effort_item_id: int = Field(..., description="ID of the reporting effort item")


class ReportingEffortItemTrackerUpdate(ReportingEffortItemTrackerBase):
    """Schema for updating a ReportingEffortItemTracker."""
    pass


class ReportingEffortItemTrackerInDB(ReportingEffortItemTrackerBase):
    """Schema for ReportingEffortItemTracker from database."""

    id: int
    reporting_effort_item_id: int
    unresolved_comment_count: int = Field(0, description="Count of unresolved comments")
    unresolved_biostat_comment_count: int = Field(0, description="Count of unresolved biostat comments")
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class ReportingEffortItemTracker(ReportingEffortItemTrackerInDB):
    """Schema for ReportingEffortItemTracker response."""
    pass


class ReportingEffortItemTrackerWithDetails(ReportingEffortItemTrackerInDB):
    """Schema for ReportingEffortItemTracker with user details."""

    production_programmer_name: Optional[str] = None
    qc_programmer_name: Optional[str] = None
    biostat_reviewer_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)