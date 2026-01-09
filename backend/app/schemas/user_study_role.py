"""Schemas for UserStudyRole - study-scoped access control."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

from app.models.user_study_role import StudyRole


class UserStudyRoleBase(BaseModel):
    """Base schema for UserStudyRole."""
    user_id: int = Field(..., description="User ID")
    study_id: int = Field(..., description="Study ID")
    role: StudyRole = Field(default=StudyRole.VIEWER, description="User's role in the study")


class UserStudyRoleCreate(UserStudyRoleBase):
    """Schema for creating a UserStudyRole."""
    pass


class UserStudyRoleUpdate(BaseModel):
    """Schema for updating a UserStudyRole."""
    role: StudyRole = Field(..., description="New role for the user in the study")


class UserStudyRoleInDBBase(UserStudyRoleBase):
    """Base schema for UserStudyRole from database."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserStudyRole(UserStudyRoleInDBBase):
    """Schema for UserStudyRole response."""
    pass


class UserStudyRoleInDB(UserStudyRoleInDBBase):
    """Schema for UserStudyRole in database."""
    pass


# Extended schemas with related entity information

class UserStudyRoleWithUser(UserStudyRoleInDBBase):
    """UserStudyRole with user details."""
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(None, description="User email")

    model_config = ConfigDict(from_attributes=True)


class UserStudyRoleWithStudy(UserStudyRoleInDBBase):
    """UserStudyRole with study details."""
    study_label: str = Field(..., description="Study label")

    model_config = ConfigDict(from_attributes=True)


# Request/Response schemas for API endpoints

class AssignStudyRoleRequest(BaseModel):
    """Request schema for assigning a user role to a study."""
    user_id: int = Field(..., description="User ID to assign")
    role: StudyRole = Field(..., description="Role to assign")


class BulkAssignStudyRolesRequest(BaseModel):
    """Request schema for bulk assigning roles to a study."""
    assignments: List[AssignStudyRoleRequest] = Field(..., description="List of role assignments")


class StudyMember(BaseModel):
    """Schema for a study member with their role."""
    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(None, description="User email")
    role: StudyRole = Field(..., description="User's role in the study")
    is_admin: bool = Field(..., description="Whether user is a global administrator")
    is_explicit_assignment: bool = Field(..., description="Whether this is an explicit assignment or default access")
    assigned_at: Optional[datetime] = Field(None, description="When the role was assigned")

    model_config = ConfigDict(from_attributes=True)


class StudyMembersResponse(BaseModel):
    """Response schema for listing study members."""
    study_id: int
    study_label: str
    members: List[StudyMember]
    total_count: int


class UserStudyRolesResponse(BaseModel):
    """Response schema for listing a user's study roles."""
    user_id: int
    username: str
    is_admin: bool = Field(..., description="Whether user is a global administrator")
    study_roles: List[UserStudyRoleWithStudy]


class StudyPermissions(BaseModel):
    """Schema for current user's permissions in a study."""
    study_id: int
    role: StudyRole
    can_view: bool
    can_edit: bool
    can_bulk_assign: bool
    can_bulk_status_update: bool
    can_delete_items: bool
    can_manage_members: bool
    can_bulk_copy: bool
    can_manage_packages: bool = False
    can_manage_tfl_properties: bool = False


class MyStudyRolesResponse(BaseModel):
    """Response schema for current user's study roles."""
    is_admin: bool = Field(..., description="Whether user is a global administrator")
    lead_study_ids: List[int] = Field(..., description="List of study IDs where user has LEAD role")
    study_roles: dict = Field(..., description="Dict mapping study_id to role name")

