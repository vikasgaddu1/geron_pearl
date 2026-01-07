"""Pydantic schemas for ReportingEffort Use Cases."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
import re


# ==================== UseCase Schemas ====================

class ReportingEffortUseCaseBase(BaseModel):
    """Base schema for UseCase."""
    name: str = Field(..., min_length=1, max_length=100, description="Use case name")
    color: str = Field("#3B82F6", description="Hex color code for display")
    description: Optional[str] = Field(None, description="Optional description")

    @field_validator('color')
    @classmethod
    def validate_color(cls, v: str) -> str:
        if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError('Color must be a valid hex color (e.g., #3B82F6)')
        return v.upper()


class ReportingEffortUseCaseCreate(ReportingEffortUseCaseBase):
    """Schema for creating a new UseCase."""
    pass


class ReportingEffortUseCaseUpdate(BaseModel):
    """Schema for updating a UseCase."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Use case name")
    color: Optional[str] = Field(None, description="Hex color code for display")
    description: Optional[str] = Field(None, description="Optional description")

    @field_validator('color')
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError('Color must be a valid hex color (e.g., #3B82F6)')
        return v.upper()


class ReportingEffortUseCaseInDB(ReportingEffortUseCaseBase):
    """Schema for UseCase in database."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportingEffortUseCase(ReportingEffortUseCaseInDB):
    """Schema for UseCase response."""
    pass


class ReportingEffortUseCaseWithCount(ReportingEffortUseCase):
    """Schema for UseCase with usage count."""
    usage_count: int = Field(0, description="Number of reporting efforts using this use case")


class UseCaseSummary(BaseModel):
    """Minimal schema for embedding in other responses."""
    id: int
    name: str
    color: str

    model_config = ConfigDict(from_attributes=True)


# ==================== Assignment Schemas ====================

class UseCaseAssignmentCreate(BaseModel):
    """Schema for assigning a use case to a reporting effort."""
    reporting_effort_id: int = Field(..., gt=0)
    use_case_id: int = Field(..., gt=0)


class UseCaseAssignment(BaseModel):
    """Schema for use case assignment."""
    id: int
    reporting_effort_id: int
    use_case_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UseCaseAssignmentWithDetails(UseCaseAssignment):
    """Schema for assignment with nested use case details."""
    use_case: ReportingEffortUseCase


# ==================== Bulk Operation Schemas ====================

class BulkUseCaseAssignment(BaseModel):
    """Schema for bulk assigning a use case to multiple reporting efforts."""
    reporting_effort_ids: List[int] = Field(..., min_length=1)
    use_case_id: int = Field(..., gt=0)


class BulkUseCaseRemoval(BaseModel):
    """Schema for bulk removing a use case from multiple reporting efforts."""
    reporting_effort_ids: List[int] = Field(..., min_length=1)
    use_case_id: int = Field(..., gt=0)


class BulkOperationResult(BaseModel):
    """Result of a bulk operation."""
    success: bool
    affected_count: int
    errors: List[str] = Field(default_factory=list)
