"""Pydantic schemas for ReportingEffort."""

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

from app.schemas.reporting_effort_usecase import UseCaseSummary


class ReportingEffortBase(BaseModel):
    """Base schema for ReportingEffort."""
    study_id: int = Field(..., gt=0, description="ID of the associated study")
    database_release_id: int = Field(..., gt=0, description="ID of the associated database release")
    database_release_label: str = Field(..., min_length=1, max_length=255, description="Database release label")


class ReportingEffortCreate(ReportingEffortBase):
    """Schema for creating a new ReportingEffort."""
    pass


class ReportingEffortUpdate(BaseModel):
    """Schema for updating an existing ReportingEffort.

    Note: study_id and database_release_id are intentionally excluded
    as reporting efforts cannot be reassigned between studies or database releases after creation.
    Use cases are managed separately via the use-cases API.
    """
    database_release_label: Optional[str] = Field(None, min_length=1, max_length=255, description="Database release label")


class ReportingEffortInDB(ReportingEffortBase):
    """Schema for ReportingEffort stored in database."""
    id: int = Field(..., description="Unique identifier for the reporting effort")
    created_at: datetime = Field(..., description="Timestamp when the reporting effort was created")
    updated_at: datetime = Field(..., description="Timestamp when the reporting effort was last updated")

    model_config = ConfigDict(from_attributes=True)


class ReportingEffort(ReportingEffortInDB):
    """Schema for ReportingEffort response with expanded details."""
    # Optional expanded fields for better UI filtering
    study_label: Optional[str] = Field(None, description="Label of the associated study")
    database_release_label_full: Optional[str] = Field(None, description="Label of the associated database release")
    # Use cases assigned to this reporting effort
    use_cases: List[UseCaseSummary] = Field(default_factory=list, description="Use cases assigned to this effort")
    # Lock status fields
    is_locked: bool = Field(False, description="Whether the reporting effort is locked")
    locked_at: Optional[datetime] = Field(None, description="When the reporting effort was locked/unlocked")
    locked_by_id: Optional[int] = Field(None, description="User ID who locked/unlocked")
    locked_by_username: Optional[str] = Field(None, description="Username of user who locked/unlocked")
    lock_reason: Optional[str] = Field(None, description="Reason for the lock/unlock")
    # Signature status fields (permanent, unlike lock)
    is_signed: bool = Field(False, description="Whether the reporting effort has been signed")
    signed_at: Optional[datetime] = Field(None, description="When the reporting effort was signed")
    signed_by_id: Optional[int] = Field(None, description="User ID who signed")
    signed_by_username: Optional[str] = Field(None, description="Username of signer")
    signature_reason: Optional[str] = Field(None, description="Reason provided for signing")

    model_config = ConfigDict(from_attributes=True)


# ==================== Lock Request/Response Schemas ====================


class ReportingEffortLockRequest(BaseModel):
    """Schema for locking/unlocking a reporting effort."""
    reason: str = Field(..., min_length=1, max_length=1000, description="Required reason for the lock/unlock action")


class ReportingEffortLockHistoryEntry(BaseModel):
    """Schema for a single lock history entry."""
    id: int = Field(..., description="Unique identifier for the history entry")
    action: str = Field(..., description="Action performed: LOCK or UNLOCK")
    reason: str = Field(..., description="Reason provided for the action")
    performed_by_id: int = Field(..., description="User ID who performed the action")
    performed_by_username: str = Field(..., description="Username of user who performed the action")
    created_at: datetime = Field(..., description="When the action was performed")

    model_config = ConfigDict(from_attributes=True)


# ==================== Electronic Signature Schemas ====================


class ReportingEffortSignRequest(BaseModel):
    """Schema for signing a reporting effort."""
    totp_token: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit TOTP code from authenticator app"
    )
    reason: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Required reason/intent for signing (min 10 chars)"
    )


class ReportingEffortSignatureHistoryEntry(BaseModel):
    """Schema for a single signature history entry."""
    id: int = Field(..., description="Unique identifier for the history entry")
    signed_by_id: Optional[int] = Field(None, description="User ID who signed")
    signed_by_username: str = Field(..., description="Username of signer (preserved)")
    signature_hash: str = Field(..., description="SHA256 hash for verification")
    reason: str = Field(..., description="Reason provided for signing")
    items_count: int = Field(..., description="Number of items at signing time")
    created_at: datetime = Field(..., description="When the signature was created")
    ip_address: Optional[str] = Field(None, description="IP address of signer")

    model_config = ConfigDict(from_attributes=True)


class SignatureReadinessResponse(BaseModel):
    """Response for signature readiness check."""
    can_sign: bool = Field(..., description="Whether signing is possible")
    is_signed: bool = Field(False, description="Whether already signed")
    has_totp_setup: bool = Field(False, description="Whether user has TOTP configured")
    is_responsible: bool = Field(False, description="Whether user is admin or study LEAD")
    all_items_in_production: bool = Field(False, description="Whether all items are in production")
    total_items: int = Field(0, description="Total items in effort")
    items_in_production: int = Field(0, description="Items with in_production_flag=True")
    is_locked_out: bool = Field(False, description="Whether user is locked out from signing")
    lockout_remaining_minutes: int = Field(0, description="Minutes until lockout expires")
    blockers: List[str] = Field(default_factory=list, description="List of reasons preventing signing")
    signed_by_username: Optional[str] = Field(None, description="Username of signer (if signed)")
    signed_at: Optional[datetime] = Field(None, description="When signed (if signed)")


class SignatureVerificationResponse(BaseModel):
    """Response from signature verification."""
    is_valid: bool = Field(..., description="Whether signature hash is valid")
    signed_at: Optional[datetime] = Field(None, description="When signed")
    signed_by_username: Optional[str] = Field(None, description="Username of signer")
    items_match: bool = Field(False, description="Whether current items match signed snapshot")
    items_at_signing: int = Field(0, description="Number of items when signed")
    items_current: int = Field(0, description="Current number of items")