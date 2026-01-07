"""Implementation Guide Version Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field, ConfigDict, field_validator


class IGVersionBase(BaseModel):
    """Base IGVersion schema with required fields."""
    
    standard_type: Literal["SDTM", "ADaM"] = Field(
        ...,
        description="Type of standard: SDTM or ADaM"
    )
    version: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Version number (e.g., 3.2, 3.3, 1.1)"
    )
    description: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional description for this version"
    )
    is_active: bool = Field(
        True,
        description="Whether this version is available for selection"
    )
    
    @field_validator('version')
    @classmethod
    def clean_version(cls, v: str) -> str:
        """Remove leading 'v' or 'V' if present."""
        if v and v.lower().startswith('v'):
            return v[1:]
        return v


class IGVersionCreate(IGVersionBase):
    """Schema for creating a new IG version."""
    pass


class IGVersionUpdate(BaseModel):
    """Schema for updating an IG version. All fields optional for partial updates."""
    
    standard_type: Optional[Literal["SDTM", "ADaM"]] = Field(
        None,
        description="Type of standard: SDTM or ADaM"
    )
    version: Optional[str] = Field(
        None,
        min_length=1,
        max_length=20,
        description="Version number (e.g., 3.2, 3.3, 1.1)"
    )
    description: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional description for this version"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Whether this version is available for selection"
    )
    
    @field_validator('version')
    @classmethod
    def clean_version(cls, v: Optional[str]) -> Optional[str]:
        """Remove leading 'v' or 'V' if present."""
        if v and v.lower().startswith('v'):
            return v[1:]
        return v


class IGVersionInDB(IGVersionBase):
    """Schema representing IG version as stored in database."""
    
    id: int = Field(..., description="IG version ID")
    created_at: datetime = Field(..., description="Timestamp when created")
    updated_at: datetime = Field(..., description="Timestamp when last updated")
    
    model_config = ConfigDict(from_attributes=True)


class IGVersion(IGVersionInDB):
    """Schema for IG version responses."""
    
    model_config = ConfigDict(from_attributes=True)






