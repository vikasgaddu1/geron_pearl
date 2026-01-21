"""Pydantic schemas for Feature Request / Bug Report."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

from app.models.feature_request import FeatureRequestStatus, FeatureRequestCategory


class FeatureRequestBase(BaseModel):
    """Base feature request schema with common fields."""
    category: FeatureRequestCategory
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)


class FeatureRequestCreate(FeatureRequestBase):
    """Schema for creating a feature request (tenant user)."""
    pass


class FeatureRequestUpdate(BaseModel):
    """Schema for updating a feature request (super admin)."""
    status: Optional[FeatureRequestStatus] = None
    admin_response: Optional[str] = None


class FeatureRequestInDB(FeatureRequestBase):
    """Schema for feature request stored in database."""
    id: int
    tenant_id: int
    user_id: int
    status: FeatureRequestStatus
    admin_response: Optional[str] = None
    responded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class FeatureRequest(FeatureRequestInDB):
    """Full feature request schema with all fields."""
    pass


class FeatureRequestWithUser(FeatureRequest):
    """Feature request with user details (for super admin view)."""
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    tenant_name: Optional[str] = None


class FeatureRequestListResponse(BaseModel):
    """Paginated list response for feature requests."""
    items: List[FeatureRequestWithUser]
    total: int
    skip: int
    limit: int


class FeatureRequestStatsResponse(BaseModel):
    """Stats response for feature request counts by status."""
    pending: int
    working: int
    done: int
    total: int
