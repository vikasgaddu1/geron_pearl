"""Package Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, Field, ConfigDict


class PackageBase(BaseModel):
    """Base Package schema with common fields."""
    
    package_name: str = Field(..., min_length=1, max_length=255, description="Package name")


class PackageCreate(PackageBase):
    """Schema for creating a new package."""
    
    pass


class PackageUpdate(BaseModel):
    """Schema for updating an existing package."""
    
    package_name: str = Field(..., min_length=1, max_length=255, description="Package name")


class PackageInDB(PackageBase):
    """Schema representing a package as stored in database."""
    
    id: int = Field(..., description="Package ID")
    created_at: datetime = Field(..., description="Timestamp when the package was created")
    updated_at: datetime = Field(..., description="Timestamp when the package was last updated")
    
    model_config = ConfigDict(from_attributes=True)


class Package(PackageInDB):
    """Schema for package responses."""
    
    pass


class PackageWithItems(Package):
    """Schema for package with its items."""
    
    package_items: List[Any] = Field(default_factory=list, description="List of package items")
    
    model_config = ConfigDict(from_attributes=True)