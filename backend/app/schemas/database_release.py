"""DatabaseRelease Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class DatabaseReleaseBase(BaseModel):
    """Base DatabaseRelease schema with common fields."""
    
    study_id: int = Field(..., gt=0, description="Study ID")
    database_release_label: str = Field(..., min_length=1, max_length=255, description="Database release label")


class DatabaseReleaseCreate(DatabaseReleaseBase):
    """Schema for creating a new database release."""
    
    pass


class DatabaseReleaseUpdate(BaseModel):
    """Schema for updating an existing database release."""
    
    database_release_label: str = Field(..., min_length=1, max_length=255, description="Database release label")


class DatabaseReleaseInDB(DatabaseReleaseBase):
    """Schema representing a database release as stored in database."""
    
    id: int = Field(..., description="Database release ID")
    created_at: datetime = Field(..., description="Timestamp when the database release was created")
    updated_at: datetime = Field(..., description="Timestamp when the database release was last updated")
    
    model_config = ConfigDict(from_attributes=True)


class DatabaseRelease(DatabaseReleaseInDB):
    """Schema for database release responses."""
    
    pass