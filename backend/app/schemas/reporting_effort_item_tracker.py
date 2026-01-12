"""Pydantic schemas for ReportingEffortItemTracker."""

from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict

from app.models.reporting_effort_item_tracker import ProductionStatus, QCStatus



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
    
    model_config = ConfigDict(from_attributes=True)