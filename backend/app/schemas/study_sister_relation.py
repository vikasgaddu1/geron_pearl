"""Schemas for StudySisterRelation - code reuse tracking between studies."""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime


class StudySisterRelationBase(BaseModel):
    """Base schema for StudySisterRelation."""
    primary_study_id: int = Field(..., description="Study that will reuse code")
    sister_study_id: int = Field(..., description="Study providing reusable code")
    code_reuse_percentage: int = Field(
        default=50, 
        ge=0, 
        le=100,
        description="Estimated percentage of code that can be reused (0-100)"
    )
    notes: Optional[str] = Field(None, description="Description of what is being reused")
    reusable_components: Optional[str] = Field(
        None, 
        description="Types of reusable components: SDTM_specs, ADaM_specs, TLF_shells, macros"
    )

    @field_validator('primary_study_id', 'sister_study_id')
    @classmethod
    def validate_study_ids(cls, v: int, info) -> int:
        if v <= 0:
            raise ValueError("Study ID must be positive")
        return v


class StudySisterRelationCreate(StudySisterRelationBase):
    """Schema for creating a StudySisterRelation."""
    pass


class StudySisterRelationUpdate(BaseModel):
    """Schema for updating a StudySisterRelation."""
    code_reuse_percentage: Optional[int] = Field(None, ge=0, le=100)
    notes: Optional[str] = None
    reusable_components: Optional[str] = None


class StudySisterRelationInDB(StudySisterRelationBase):
    """Schema for StudySisterRelation from database."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudySisterRelation(StudySisterRelationInDB):
    """Schema for StudySisterRelation response."""
    effort_reduction_factor: float = Field(
        ..., 
        description="Multiplier for estimates (e.g., 0.58 = 58% of original)"
    )


class StudySisterRelationWithStudies(StudySisterRelationInDB):
    """StudySisterRelation with study details."""
    primary_study_label: str
    sister_study_label: str
    effort_reduction_factor: float

    model_config = ConfigDict(from_attributes=True)


# Request/Response schemas

class CreateSisterRelationRequest(BaseModel):
    """Request schema for creating a sister study relationship."""
    sister_study_id: int = Field(..., description="ID of the sister study")
    code_reuse_percentage: int = Field(default=50, ge=0, le=100)
    notes: Optional[str] = None
    reusable_components: Optional[str] = None


class SisterStudyInfo(BaseModel):
    """Info about a sister study for display."""
    study_id: int
    study_label: str
    code_reuse_percentage: int
    effort_reduction_factor: float
    reusable_components: Optional[str] = None
    notes: Optional[str] = None


class StudySisterRelationsResponse(BaseModel):
    """Response showing all sister study relationships for a study."""
    study_id: int
    study_label: str
    can_reuse_from: List[SisterStudyInfo] = Field(
        ..., 
        description="Studies this study can reuse code FROM"
    )
    provides_code_to: List[SisterStudyInfo] = Field(
        ..., 
        description="Studies that reuse code FROM this study"
    )


class EstimateAdjustmentPreview(BaseModel):
    """Preview of how sister study affects estimates."""
    original_estimate_hours: float
    adjusted_estimate_hours: float
    reduction_percentage: float
    sister_study_label: str
    code_reuse_percentage: int

