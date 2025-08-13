"""Pydantic schemas for AuditLog."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AuditLogBase(BaseModel):
    """Base schema for AuditLog."""
    
    table_name: str = Field(..., max_length=100, description="Name of the table that was modified")
    record_id: int = Field(..., description="ID of the record that was modified")
    action: str = Field(..., max_length=50, description="Action performed: CREATE, UPDATE, DELETE")
    changes_json: Optional[str] = Field(None, description="JSON representation of the changes made")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP address of the user")
    user_agent: Optional[str] = Field(None, description="User agent string from the request")


class AuditLogCreate(AuditLogBase):
    """Schema for creating an AuditLog entry."""
    
    user_id: Optional[int] = Field(None, description="User who performed the action")


class AuditLogInDB(AuditLogBase):
    """Schema for AuditLog from database."""
    
    id: int
    user_id: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AuditLog(AuditLogInDB):
    """Schema for AuditLog response."""
    pass


class AuditLogWithDetails(AuditLogInDB):
    """Schema for AuditLog with user details."""
    
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)