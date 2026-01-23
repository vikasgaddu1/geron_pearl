from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    username: str = Field(..., min_length=1, description="Username must be at least 1 character")
    is_admin: bool = Field(default=False, description="Whether user has global admin privileges")
    department: Optional[str] = Field(None, description="User department")


class UserCreate(UserBase):
    email: EmailStr = Field(..., description="User email address (required for authentication)")
    password: str = Field(..., min_length=8, max_length=100, description="User password (minimum 8 characters)")
    generate_password: Optional[bool] = Field(False, description="Whether to auto-generate password (client-side)")


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=1)
    email: Optional[EmailStr] = Field(None, description="User email address")
    password: Optional[str] = Field(None, min_length=8, max_length=100, description="New password (optional, only set if provided)")
    is_admin: Optional[bool] = Field(None, description="Whether user has global admin privileges")
    department: Optional[str] = None


class UserInDBBase(UserBase):
    id: int
    email: Optional[str] = Field(default=None, description="User email address")
    is_active: bool = Field(default=True, description="Whether the user account is active")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    pass


# ==================== Electronic Signature TOTP Schemas ====================


class SignatureSetupResponse(BaseModel):
    """Response from starting signature TOTP setup."""
    provisioning_uri: str = Field(..., description="URI for QR code (otpauth://...)")
    backup_codes: List[str] = Field(..., description="10 one-time backup codes")
    message: str = Field(default="Scan the QR code with your authenticator app, then verify with a 6-digit code")


class SignatureVerifySetupRequest(BaseModel):
    """Request to verify TOTP setup with a code from authenticator app."""
    totp_code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit TOTP code from authenticator app"
    )


class SignatureVerifySetupResponse(BaseModel):
    """Response from successful TOTP verification."""
    success: bool = Field(..., description="Whether setup was completed successfully")
    message: str = Field(default="Signature authentication setup complete")


class SignatureStatusResponse(BaseModel):
    """Response showing current signature TOTP status."""
    is_setup_completed: bool = Field(..., description="Whether TOTP setup is completed")
    is_locked_out: bool = Field(False, description="Whether user is locked out from signing")
    lockout_remaining_minutes: int = Field(0, description="Minutes until lockout expires")
    failed_attempts: int = Field(0, description="Current failed attempt count")


class SignatureUseBackupCodeRequest(BaseModel):
    """Request to use a backup code for signing."""
    backup_code: str = Field(
        ...,
        min_length=8,
        max_length=12,
        description="One-time backup code"
    )


class SignatureUseBackupCodeResponse(BaseModel):
    """Response from using a backup code."""
    success: bool = Field(..., description="Whether backup code was valid")
    remaining_codes: int = Field(..., description="Number of backup codes remaining")
    message: str = Field(default="Backup code accepted")