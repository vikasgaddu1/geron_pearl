"""Study Pydantic schemas for request/response validation."""

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
    
    study_label: Optional[str] = Field(None, min_length=1, max_length=255, description="Study label")


class StudyInDB(StudyBase):
    """Schema representing a study as stored in database."""
    
    id: int = Field(..., description="Study ID")
    
    model_config = ConfigDict(from_attributes=True)


class Study(StudyInDB):
    """Schema for study responses."""
    
    pass