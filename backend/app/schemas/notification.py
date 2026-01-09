"""Pydantic schemas for Notification."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class NotificationBase(BaseModel):
    """Base notification schema with common fields."""
    notification_type: str
    title: str
    message: str
    item_code: Optional[str] = None
    study_label: Optional[str] = None


class NotificationCreate(NotificationBase):
    """Schema for creating a notification."""
    user_id: int
    tracker_id: Optional[int] = None
    triggered_by_user_id: Optional[int] = None


class NotificationUpdate(BaseModel):
    """Schema for updating a notification."""
    is_read: Optional[bool] = None
    is_acknowledged: Optional[bool] = None


class NotificationInDB(NotificationBase):
    """Schema for notification stored in database."""
    id: int
    user_id: int
    tracker_id: Optional[int] = None
    triggered_by_user_id: Optional[int] = None
    is_read: bool
    is_acknowledged: bool
    created_at: datetime
    read_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class Notification(NotificationInDB):
    """Full notification schema with all fields."""
    pass


class NotificationWithDetails(Notification):
    """Notification schema with expanded user details."""
    triggered_by_username: Optional[str] = None


class NotificationCountResponse(BaseModel):
    """Schema for notification count response."""
    unread_count: int
    total_unacknowledged: int
