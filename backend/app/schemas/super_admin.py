"""Pydantic schemas for SuperAdmin."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, EmailStr


class SuperAdminBase(BaseModel):
    """Base schema for SuperAdmin."""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)


class SuperAdminCreate(SuperAdminBase):
    """Schema for creating a new super admin."""
    password: str = Field(..., min_length=12, description="Password must be at least 12 characters")


class SuperAdminUpdate(BaseModel):
    """Schema for updating a super admin."""
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    password: Optional[str] = Field(None, min_length=12)
    is_active: Optional[bool] = None


class SuperAdminResponse(SuperAdminBase):
    """Schema for super admin response (excludes sensitive fields)."""
    id: int
    mfa_enabled: bool
    is_active: bool
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    failed_login_attempts: int
    locked_until: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SuperAdminLogin(BaseModel):
    """Schema for super admin login."""
    email: EmailStr
    password: str
    mfa_code: Optional[str] = Field(None, min_length=6, max_length=6, description="6-digit TOTP code")


class SuperAdminLoginResponse(BaseModel):
    """Schema for super admin login response."""
    access_token: str
    token_type: str = "bearer"
    requires_mfa: bool = False
    admin: Optional[SuperAdminResponse] = None


class MFASetupResponse(BaseModel):
    """Schema for MFA setup response."""
    secret: str
    qr_code_url: str
    backup_codes: list[str]


class MFAVerifyRequest(BaseModel):
    """Schema for MFA verification."""
    code: str = Field(..., min_length=6, max_length=6)


class ImpersonationRequest(BaseModel):
    """Schema for impersonation request."""
    tenant_id: int


class ImpersonationResponse(BaseModel):
    """Schema for impersonation response."""
    impersonation_token: str
    original_token: str
    tenant_name: str
    expires_at: datetime
