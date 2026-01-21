"""Pydantic schemas for StudyDefaultBiostat."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class StudyDefaultBiostatBase(BaseModel):
    """Base schema for StudyDefaultBiostat."""

    user_id: int = Field(..., description="User ID of the default biostat reviewer")
    is_active: bool = Field(True, description="Whether this is the active default biostat")


class StudyDefaultBiostatCreate(StudyDefaultBiostatBase):
    """Schema for creating a StudyDefaultBiostat."""

    study_id: int = Field(..., description="ID of the study")


class StudyDefaultBiostatUpdate(BaseModel):
    """Schema for updating a StudyDefaultBiostat."""

    user_id: Optional[int] = Field(None, description="User ID of the default biostat reviewer")
    is_active: Optional[bool] = Field(None, description="Whether this is the active default biostat")


class StudyDefaultBiostatInDB(StudyDefaultBiostatBase):
    """Schema for StudyDefaultBiostat from database."""

    id: int
    study_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class StudyDefaultBiostat(StudyDefaultBiostatInDB):
    """Schema for StudyDefaultBiostat response."""
    pass


class StudyDefaultBiostatWithUser(StudyDefaultBiostatInDB):
    """Schema for StudyDefaultBiostat with user details."""

    user_name: Optional[str] = Field(None, description="Name of the default biostat user")
    user_email: Optional[str] = Field(None, description="Email of the default biostat user")

    model_config = ConfigDict(from_attributes=True)
