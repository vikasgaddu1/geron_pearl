"""AcronymSetMember Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, ConfigDict

if TYPE_CHECKING:
    from app.schemas.acronym import Acronym
    from app.schemas.acronym_set import AcronymSet


class AcronymSetMemberBase(BaseModel):
    """Base AcronymSetMember schema with common fields."""
    
    acronym_set_id: int = Field(..., gt=0, description="ID of the acronym set")
    acronym_id: int = Field(..., gt=0, description="ID of the acronym")
    sort_order: int = Field(default=0, description="Sort order for consistent presentation")


class AcronymSetMemberCreate(AcronymSetMemberBase):
    """Schema for creating a new acronym set member."""
    
    pass


class AcronymSetMemberUpdate(BaseModel):
    """Schema for updating an existing acronym set member."""
    
    sort_order: Optional[int] = Field(None, description="Sort order for consistent presentation")


class AcronymSetMemberInDB(AcronymSetMemberBase):
    """Schema representing an acronym set member as stored in database."""
    
    id: int = Field(..., description="Acronym set member ID")
    created_at: datetime = Field(..., description="Timestamp when the member was added")
    updated_at: datetime = Field(..., description="Timestamp when the member was last updated")
    
    model_config = ConfigDict(from_attributes=True)


class AcronymSetMember(AcronymSetMemberInDB):
    """Schema for acronym set member responses."""
    
    pass


# Extended schemas with relationships
class AcronymSetMemberWithAcronym(AcronymSetMember):
    """Schema for acronym set member with acronym details."""
    
    acronym: "Acronym" = Field(..., description="Acronym details")


class AcronymSetMemberWithSet(AcronymSetMember):
    """Schema for acronym set member with set details."""
    
    acronym_set: "AcronymSet" = Field(..., description="Acronym set details")


class AcronymSetMemberWithBoth(AcronymSetMember):
    """Schema for acronym set member with both acronym and set details."""
    
    acronym: "Acronym" = Field(..., description="Acronym details")
    acronym_set: "AcronymSet" = Field(..., description="Acronym set details")


# Forward reference resolution - import at the end to avoid circular imports
from app.schemas.acronym import Acronym
from app.schemas.acronym_set import AcronymSet

AcronymSetMemberWithAcronym.model_rebuild()
AcronymSetMemberWithSet.model_rebuild()
AcronymSetMemberWithBoth.model_rebuild()