"""Study Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class StudyBase(BaseModel):
    """Base Study schema with common fields."""
    
    study_label: str = Field(..., min_length=1, max_length=255, description="Study label")


class StudyCreate(StudyBase):
    """Schema for creating a new study."""
    
    pass


class StudyUpdate(BaseModel):
    """Schema for updating an existing study."""
    
    study_label: str = Field(..., min_length=1, max_length=255, description="Study label")


class StudyInDB(StudyBase):
    """Schema representing a study as stored in database."""
    
    id: int = Field(..., description="Study ID")
    created_at: datetime = Field(..., description="Timestamp when the study was created")
    updated_at: datetime = Field(..., description="Timestamp when the study was last updated")
    
    model_config = ConfigDict(from_attributes=True)


class Study(StudyInDB):
    """Schema for study responses."""
    
    pass


class BulkHierarchyRow(BaseModel):
    """One row for bulk study/release/effort upload."""
    study_label: str = Field(..., min_length=1, max_length=255, description="Study label")
    database_release_label: str = Field(..., min_length=1, max_length=255, description="Database release label")
    reporting_effort_label: str = Field(..., min_length=1, max_length=255, description="Reporting effort label")


class BulkHierarchyResponse(BaseModel):
    """Result of bulk study/release/effort upload."""
    success: bool
    created_studies: int
    created_releases: int
    created_efforts: int
    skipped_duplicates: int
    errors: list[str] = Field(default_factory=list)