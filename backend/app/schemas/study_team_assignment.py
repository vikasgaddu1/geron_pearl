"""Schemas for StudyTeamAssignment - team allocation tracking."""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime, date

from app.models.study_team_assignment import JobType, ExperienceLevel, DepartureReason


class StudyTeamAssignmentBase(BaseModel):
    """Base schema for StudyTeamAssignment."""
    user_id: int = Field(..., description="User ID")
    study_id: int = Field(..., description="Study ID")
    job_type: str = Field(..., description="Job type: LEAD, PRODUCTION_PROGRAMMER, QC_PROGRAMMER")
    allocation_percentage: int = Field(
        default=100, 
        ge=1, 
        le=100,
        description="Percentage of time allocated to this study (1-100)"
    )
    productive_time_factor: int = Field(
        default=75,
        ge=1,
        le=100,
        description="Percentage of allocated time that is productive/trackable (typically 75-80%)"
    )
    experience_level: str = Field(
        default="MID",
        description="Experience level: JUNIOR, MID, SENIOR"
    )
    effective_start_date: date = Field(..., description="Date this allocation becomes effective")
    effective_end_date: Optional[date] = Field(None, description="Date this allocation ends (null = still active)")
    notes: Optional[str] = Field(None, description="Optional notes about this assignment")

    @field_validator('job_type')
    @classmethod
    def validate_job_type(cls, v: str) -> str:
        valid_types = [jt.value for jt in JobType]
        if v not in valid_types:
            raise ValueError(f"job_type must be one of: {valid_types}")
        return v

    @field_validator('experience_level')
    @classmethod
    def validate_experience_level(cls, v: str) -> str:
        valid_levels = [el.value for el in ExperienceLevel]
        if v not in valid_levels:
            raise ValueError(f"experience_level must be one of: {valid_levels}")
        return v


class StudyTeamAssignmentCreate(StudyTeamAssignmentBase):
    """Schema for creating a StudyTeamAssignment."""
    pass


class StudyTeamAssignmentUpdate(BaseModel):
    """Schema for updating a StudyTeamAssignment.
    
    Note: Most updates should create a new record instead (to preserve history).
    This is mainly for correcting data entry errors.
    """
    job_type: Optional[str] = Field(None, description="Job type")
    allocation_percentage: Optional[int] = Field(None, ge=1, le=100)
    productive_time_factor: Optional[int] = Field(None, ge=1, le=100)
    experience_level: Optional[str] = None
    effective_start_date: Optional[date] = None
    effective_end_date: Optional[date] = None
    notes: Optional[str] = None

    @field_validator('job_type')
    @classmethod
    def validate_job_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_types = [jt.value for jt in JobType]
        if v not in valid_types:
            raise ValueError(f"job_type must be one of: {valid_types}")
        return v

    @field_validator('experience_level')
    @classmethod
    def validate_experience_level(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_levels = [el.value for el in ExperienceLevel]
        if v not in valid_levels:
            raise ValueError(f"experience_level must be one of: {valid_levels}")
        return v


class StudyTeamAssignmentInDBBase(StudyTeamAssignmentBase):
    """Base schema for StudyTeamAssignment from database."""
    id: int
    is_active: bool
    departure_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudyTeamAssignment(StudyTeamAssignmentInDBBase):
    """Schema for StudyTeamAssignment response."""
    pass


class StudyTeamAssignmentInDB(StudyTeamAssignmentInDBBase):
    """Schema for StudyTeamAssignment in database."""
    pass


# Extended schemas with related entity information

class StudyTeamAssignmentWithUser(StudyTeamAssignmentInDBBase):
    """StudyTeamAssignment with user details."""
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(None, description="User email")

    model_config = ConfigDict(from_attributes=True)


class StudyTeamAssignmentWithStudy(StudyTeamAssignmentInDBBase):
    """StudyTeamAssignment with study details."""
    study_label: str = Field(..., description="Study label")

    model_config = ConfigDict(from_attributes=True)


# Request/Response schemas for API endpoints

class CreateTeamAssignmentRequest(BaseModel):
    """Request schema for adding a team member to a study."""
    user_id: int = Field(..., description="User ID to assign")
    job_type: str = Field(..., description="Job type: LEAD, PRODUCTION_PROGRAMMER, QC_PROGRAMMER")
    allocation_percentage: int = Field(default=100, ge=1, le=100)
    productive_time_factor: int = Field(default=75, ge=1, le=100)
    experience_level: str = Field(default="MID")
    effective_start_date: date = Field(..., description="Start date for this assignment")
    notes: Optional[str] = None

    @field_validator('job_type')
    @classmethod
    def validate_job_type(cls, v: str) -> str:
        valid_types = [jt.value for jt in JobType]
        if v not in valid_types:
            raise ValueError(f"job_type must be one of: {valid_types}")
        return v

    @field_validator('experience_level')
    @classmethod
    def validate_experience_level(cls, v: str) -> str:
        valid_levels = [el.value for el in ExperienceLevel]
        if v not in valid_levels:
            raise ValueError(f"experience_level must be one of: {valid_levels}")
        return v


class ChangeAllocationRequest(BaseModel):
    """Request schema for changing a team member's allocation.
    
    This will close the current assignment and create a new one.
    """
    new_allocation_percentage: int = Field(..., ge=1, le=100, description="New allocation percentage")
    new_productive_time_factor: Optional[int] = Field(None, ge=1, le=100)
    new_experience_level: Optional[str] = None
    new_job_type: Optional[str] = None
    effective_date: date = Field(..., description="Date the change becomes effective")
    notes: Optional[str] = None

    @field_validator('new_job_type')
    @classmethod
    def validate_job_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_types = [jt.value for jt in JobType]
        if v not in valid_types:
            raise ValueError(f"job_type must be one of: {valid_types}")
        return v

    @field_validator('new_experience_level')
    @classmethod
    def validate_experience_level(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_levels = [el.value for el in ExperienceLevel]
        if v not in valid_levels:
            raise ValueError(f"experience_level must be one of: {valid_levels}")
        return v


class EndAssignmentRequest(BaseModel):
    """Request schema for ending a team assignment."""
    effective_date: date = Field(..., description="Date the assignment ends")
    departure_reason: str = Field(..., description="Reason: allocation_changed, reassigned_fully, left_organization, etc.")
    notes: Optional[str] = None

    @field_validator('departure_reason')
    @classmethod
    def validate_departure_reason(cls, v: str) -> str:
        valid_reasons = [dr.value for dr in DepartureReason]
        if v not in valid_reasons:
            raise ValueError(f"departure_reason must be one of: {valid_reasons}")
        return v


class TeamMemberSummary(BaseModel):
    """Summary of a team member's current allocation on a study."""
    user_id: int
    username: str
    email: Optional[str] = None
    job_type: str
    allocation_percentage: int
    productive_time_factor: int
    experience_level: str
    effective_start_date: date
    is_active: bool
    effective_weekly_hours: float = Field(..., description="Calculated productive hours per week")
    assignment_id: int = Field(..., description="Current assignment record ID")

    model_config = ConfigDict(from_attributes=True)


class StudyTeamResponse(BaseModel):
    """Response schema for listing a study's team members."""
    study_id: int
    study_label: str
    active_members: List[TeamMemberSummary]
    total_allocation_percentage: int = Field(..., description="Sum of all active member allocations")
    total_weekly_capacity_hours: float = Field(..., description="Total productive hours per week")
    member_count: int


class UserAssignmentsResponse(BaseModel):
    """Response schema for listing a user's study assignments."""
    user_id: int
    username: str
    active_assignments: List[StudyTeamAssignmentWithStudy]
    total_allocation_percentage: int = Field(..., description="Sum of allocations across all studies")
    is_over_allocated: bool = Field(..., description="True if total allocation > 100%")


class AllocationHistoryResponse(BaseModel):
    """Response schema for a user's allocation history on a study."""
    user_id: int
    username: str
    study_id: int
    study_label: str
    assignments: List[StudyTeamAssignment] = Field(..., description="All assignment records, ordered by date")


class OrphanedItemsWarning(BaseModel):
    """Warning about items assigned to inactive team members."""
    user_id: int
    username: str
    study_id: int
    study_label: str
    departure_reason: Optional[str]
    departure_date: Optional[date]
    orphaned_item_count: int = Field(..., description="Number of items still assigned to this inactive member")
    item_ids: List[int] = Field(..., description="IDs of tracker items needing reassignment")

