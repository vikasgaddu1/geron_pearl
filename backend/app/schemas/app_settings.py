"""Application Settings Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class AppSettingsBase(BaseModel):
    """Base AppSettings schema with all configurable fields."""

    default_due_date_offset: int = Field(
        default=7,
        ge=1,
        le=365,
        description="Default number of days to add when auto-setting due dates"
    )


class AppSettingsUpdate(BaseModel):
    """Schema for updating settings. All fields optional for partial updates."""

    default_due_date_offset: Optional[int] = Field(
        default=None,
        ge=1,
        le=365,
        description="Default number of days to add when auto-setting due dates"
    )


class AppSettingsInDB(AppSettingsBase):
    """Schema representing settings as stored in database."""

    id: int = Field(..., description="Settings ID (always 1)")
    updated_by_user_id: Optional[int] = Field(None, description="ID of user who last updated")
    created_at: datetime = Field(..., description="Timestamp when settings were created")
    updated_at: datetime = Field(..., description="Timestamp when settings were last updated")

    model_config = ConfigDict(from_attributes=True)


class AppSettings(AppSettingsInDB):
    """Schema for settings responses with additional computed fields."""

    updated_by_username: Optional[str] = Field(None, description="Username of user who last updated")

    model_config = ConfigDict(from_attributes=True)
