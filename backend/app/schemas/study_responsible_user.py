"""Schemas for StudyResponsibleUser - study responsibility assignment."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class StudyResponsibleUserBase(BaseModel):
    """Base schema for StudyResponsibleUser."""
    study_id: int = Field(..., description="Study ID")
    user_id: int = Field(..., description="User ID")
    is_primary: bool = Field(default=False, description="Whether this user is the primary responsible person")


class StudyResponsibleUserCreate(BaseModel):
    """Schema for creating a StudyResponsibleUser assignment."""
    user_id: int = Field(..., description="User ID to assign as responsible")
    is_primary: bool = Field(default=False, description="Whether this user is the primary responsible person")


class StudyResponsibleUserUpdate(BaseModel):
    """Schema for updating a StudyResponsibleUser assignment."""
    is_primary: Optional[bool] = Field(None, description="Update primary status")


class StudyResponsibleUserInDBBase(StudyResponsibleUserBase):
    """Base schema for StudyResponsibleUser from database."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudyResponsibleUser(StudyResponsibleUserInDBBase):
    """Schema for StudyResponsibleUser response."""
    pass


class StudyResponsibleUserInDB(StudyResponsibleUserInDBBase):
    """Schema for StudyResponsibleUser in database."""
    pass


class StudyResponsibleUserWithUser(BaseModel):
    """StudyResponsibleUser with user details for display."""
    id: int
    study_id: int
    user_id: int
    is_primary: bool
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(None, description="User email")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudyResponsibleUsersResponse(BaseModel):
    """Response schema for listing responsible users of a study."""
    study_id: int
    study_label: str
    responsible_users: List[StudyResponsibleUserWithUser]
    total_count: int


class AssignResponsibleUserRequest(BaseModel):
    """Request schema for assigning a responsible user to a study."""
    user_id: int = Field(..., description="User ID to assign as responsible")
    is_primary: bool = Field(default=False, description="Whether this user is the primary responsible person")


class UpdateResponsibleUserRequest(BaseModel):
    """Request schema for updating a responsible user's status."""
    is_primary: bool = Field(..., description="Whether this user is the primary responsible person")
