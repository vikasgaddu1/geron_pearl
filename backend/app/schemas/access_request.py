"""Pydantic schemas for AccessRequest."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

from app.models.access_request import AccessRequestType, AccessRequestStatus


class AccessRequestBase(BaseModel):
    """Base access request schema."""
    study_id: int = Field(..., description="ID of the study to request access to")
    request_type: AccessRequestType = Field(..., description="Type of access: EDITOR or RESPONSIBLE_USER")
    request_reason: Optional[str] = Field(None, max_length=1000, description="Optional reason/message for the request")


class AccessRequestCreate(AccessRequestBase):
    """Schema for creating an access request."""
    pass


class AccessRequestDeny(BaseModel):
    """Schema for denying an access request."""
    denial_reason: Optional[str] = Field(None, max_length=500, description="Reason for denial")


class AccessRequestInDB(AccessRequestBase):
    """Schema for access request stored in database."""
    id: int
    requester_id: int
    status: AccessRequestStatus
    resolved_by_id: Optional[int] = None
    resolved_at: Optional[datetime] = None
    denial_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class AccessRequestWithDetails(BaseModel):
    """Access request with expanded user and study details."""
    id: int
    requester_id: int
    study_id: int
    request_type: str  # Using str since we serialize enums to values
    status: str  # Using str since we serialize enums to values
    request_reason: Optional[str] = None
    resolved_by_id: Optional[int] = None
    resolved_at: Optional[datetime] = None
    denial_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # Expanded details
    requester_username: str
    requester_email: Optional[str] = None
    study_label: str
    resolved_by_username: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class AccessRequestListResponse(BaseModel):
    """Response for list of access requests."""
    requests: List[AccessRequestWithDetails]
    total_count: int


class PendingRequestCountResponse(BaseModel):
    """Response for pending request count."""
    pending_count: int
