"""AcronymSet Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


class AcronymSetBase(BaseModel):
    """Base AcronymSet schema with common fields."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Name of the acronym set")
    description: Optional[str] = Field(None, description="Optional description of the acronym set")


class AcronymSetCreate(AcronymSetBase):
    """Schema for creating a new acronym set."""
    
    pass


class AcronymSetUpdate(BaseModel):
    """Schema for updating an existing acronym set."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Name of the acronym set")
    description: Optional[str] = Field(None, description="Optional description of the acronym set")


class AcronymSetInDB(AcronymSetBase):
    """Schema representing an acronym set as stored in database."""
    
    id: int = Field(..., description="Acronym set ID")
    created_at: datetime = Field(..., description="Timestamp when the acronym set was created")
    updated_at: datetime = Field(..., description="Timestamp when the acronym set was last updated")
    
    model_config = ConfigDict(from_attributes=True)


class AcronymSet(AcronymSetInDB):
    """Schema for acronym set responses."""
    
    pass


# Extended schemas with relationships
class AcronymSetWithMembers(AcronymSet):
    """Schema for acronym set responses with member acronyms."""
    
    members: List["AcronymSetMemberWithAcronym"] = Field(default=[], description="List of acronyms in this set")


# Forward reference resolution
from app.schemas.acronym_set_member import AcronymSetMemberWithAcronym
AcronymSetWithMembers.model_rebuild()