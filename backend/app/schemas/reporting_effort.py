"""Pydantic schemas for ReportingEffort."""

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class ReportingEffortBase(BaseModel):
    """Base schema for ReportingEffort."""
    study_id: int = Field(..., gt=0, description="ID of the associated study")
    database_release_id: int = Field(..., gt=0, description="ID of the associated database release")
    database_release_label: str = Field(..., min_length=1, max_length=255, description="Database release label")


class ReportingEffortCreate(ReportingEffortBase):
    """Schema for creating a new ReportingEffort."""
    pass


class ReportingEffortUpdate(BaseModel):
    """Schema for updating an existing ReportingEffort.
    
    Note: study_id and database_release_id are intentionally excluded 
    as reporting efforts cannot be reassigned between studies or database releases after creation.
    """
    database_release_label: str = Field(..., min_length=1, max_length=255, description="Database release label")


class ReportingEffortInDB(ReportingEffortBase):
    """Schema for ReportingEffort stored in database."""
    id: int = Field(..., description="Unique identifier for the reporting effort")
    created_at: datetime = Field(..., description="Timestamp when the reporting effort was created")
    updated_at: datetime = Field(..., description="Timestamp when the reporting effort was last updated")

    model_config = ConfigDict(from_attributes=True)


class ReportingEffort(ReportingEffortInDB):
    """Schema for ReportingEffort response."""
    pass