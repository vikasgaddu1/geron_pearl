"""Pydantic schemas for Tracker Tags.

Schemas for tag CRUD operations and API responses.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class TrackerTagBase(BaseModel):
    """Base schema for tracker tags."""
    name: str = Field(..., min_length=1, max_length=100, description="Tag name")
    color: str = Field(
        default="#3B82F6",
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="Hex color code (e.g., '#FF5733')"
    )
    description: Optional[str] = Field(None, description="Optional tag description")


class TrackerTagCreate(TrackerTagBase):
    """Schema for creating a new tag."""
    pass


class TrackerTagUpdate(BaseModel):
    """Schema for updating a tag."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    description: Optional[str] = None


class TrackerTag(TrackerTagBase):
    """Schema for tag response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TrackerTagWithCount(TrackerTag):
    """Tag with usage count."""
    usage_count: int = Field(default=0, description="Number of trackers using this tag")


# Association schemas
class TrackerItemTagBase(BaseModel):
    """Base schema for tracker-tag association."""
    tracker_id: int = Field(..., description="Tracker ID")
    tag_id: int = Field(..., description="Tag ID")


class TrackerItemTagCreate(TrackerItemTagBase):
    """Schema for creating a tag assignment."""
    pass


class TrackerItemTag(TrackerItemTagBase):
    """Schema for tag assignment response."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TrackerItemTagWithDetails(TrackerItemTag):
    """Tag assignment with tag details."""
    tag: TrackerTag


# Bulk operations
class BulkTagAssignment(BaseModel):
    """Schema for bulk tag assignment."""
    tracker_ids: List[int] = Field(..., min_length=1, description="List of tracker IDs")
    tag_id: int = Field(..., description="Tag ID to assign")


class BulkTagRemoval(BaseModel):
    """Schema for bulk tag removal."""
    tracker_ids: List[int] = Field(..., min_length=1, description="List of tracker IDs")
    tag_id: int = Field(..., description="Tag ID to remove")


class BulkOperationResult(BaseModel):
    """Result of a bulk tag operation."""
    success: bool
    affected_count: int
    errors: List[str] = Field(default_factory=list)


# Simplified tag for embedding in tracker responses
class TagSummary(BaseModel):
    """Minimal tag info for embedding in tracker responses."""
    id: int
    name: str
    color: str
    
    model_config = ConfigDict(from_attributes=True)

