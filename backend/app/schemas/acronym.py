"""Acronym Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class AcronymBase(BaseModel):
    """Base Acronym schema with common fields."""
    
    key: str = Field(..., min_length=1, max_length=50, description="Acronym key (e.g., 'NA', 'EU')")
    value: str = Field(..., min_length=1, max_length=255, description="Acronym definition (e.g., 'North America', 'Europe')")
    description: Optional[str] = Field(None, description="Optional detailed description of the acronym")


class AcronymCreate(AcronymBase):
    """Schema for creating a new acronym."""
    
    pass


class AcronymUpdate(BaseModel):
    """Schema for updating an existing acronym."""
    
    key: Optional[str] = Field(None, min_length=1, max_length=50, description="Acronym key")
    value: Optional[str] = Field(None, min_length=1, max_length=255, description="Acronym definition")
    description: Optional[str] = Field(None, description="Optional detailed description")


class AcronymInDB(AcronymBase):
    """Schema representing an acronym as stored in database."""
    
    id: int = Field(..., description="Acronym ID")
    created_at: datetime = Field(..., description="Timestamp when the acronym was created")
    updated_at: datetime = Field(..., description="Timestamp when the acronym was last updated")
    
    model_config = ConfigDict(from_attributes=True)


class Acronym(AcronymInDB):
    """Schema for acronym responses."""
    
    pass